import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import platform
import math

# 폰트 로드
if platform.system() == 'Linux':
    plt.rcParams['font.family'] = 'NanumGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 마스터 데이터 (W, D, T 정보)
ITEM_MASTER = {
    'A': {'name': '케렌시아 1인', 'w': 550, 'd': 480, 't': 70, 'color': '#FFB6C1', 'unit': 9},
    'B': {'name': '케렌시아 3인', 'w': 1650, 'd': 680, 't': 150, 'color': '#ADD8E6', 'unit': 4},
    'C': {'name': '케렌시아 싱글', 'w': 710, 'd': 640, 't': 150, 'color': '#B0C4DE', 'unit': 4},
    'D': {'name': '케렌시아 오토만', 'w': 660, 'd': 580, 't': 150, 'color': '#FFFFE0', 'unit': 4},
    'E': {'name': '카포네 1인', 'w': 480, 'd': 435, 't': 105, 'color': '#FFE4B5', 'unit': 6},
    'F': {'name': '카포네 2인', 'w': 480, 'd': 755, 't': 105, 'color': '#FFDAB9', 'unit': 6},
    'G': {'name': '카포네 공용', 'w': 480, 'd': 375, 't': 105, 'color': '#F5DEB3', 'unit': 6},
    'H': {'name': '카포네 코너 뒤 팔걸이', 'w': 790, 'd': 465, 't': 105, 'color': '#E6E6FA', 'unit': 6},
    'I': {'name': '카포네 코너 뒤', 'w': 375, 'd': 465, 't': 105, 'color': '#D8BFD8', 'unit': 6},
    'J': {'name': '카포네 코너 팔걸이쪽', 'w': 700, 'd': 465, 't': 105, 'color': '#F0E68C', 'unit': 6}
}

def reset_inputs():
    for code in ITEM_MASTER.keys():
        st.session_state[f"input_{code}"] = 0

st.set_page_config(page_title="소파 재단 시스템", layout="wide")
st.title("🗡️ 소파 스펀지 수율 계산 자동화")

# 3. 사이드바 제어
st.sidebar.header("⚙️ 시스템 제어")
if st.sidebar.button("🧹 수량 초기화", use_container_width=True):
    reset_inputs()

st.sidebar.divider()
st.sidebar.header("📋 품목별 생산 수량 입력")

input_slots = {}
for code, info in ITEM_MASTER.items():
    if f"input_{code}" not in st.session_state: st.session_state[f"input_{code}"] = 0
    input_slots[code] = st.sidebar.number_input(f"[{code}] {info['name']} ({info['unit']}개 단위)", min_value=0, key=f"input_{code}", step=1)

# 4. 백필링 로직 (빈 곳부터 채움)
def plan_optimized_blocks(slots_dict):
    blocks = []
    temp_list = []
    for code, count in slots_dict.items():
        for _ in range(count): temp_list.append(code)
    all_req_slots = sorted(temp_list, key=lambda x: ITEM_MASTER[x]['w'] * ITEM_MASTER[x]['d'], reverse=True)
    
    for code in all_req_slots:
        info = ITEM_MASTER[code]
        # 가로/세로 중 높이를 덜 차지하는 방향 찾기
        orientations = [{'w': info['w'], 'h': info['d']}, {'w': info['d'], 'h': info['w']}]
        # B품목은 기존처럼 W를 높이로 고정
        if code == 'B': orientations = [{'w': info['d'], 'h': info['w']}]
        
        best_placement = None
        
        # 1. 기존 블록의 좁은 Side 슬롯(492)에 들어가는 최적 방향 확인
        for opt in orientations:
            for block in blocks:
                if opt['w'] <= 492 and opt['h'] <= 2384 - block["s_h"]:
                    if best_placement is None or opt['h'] < best_placement['h']:
                        best_placement = {**opt, 'block': block, 'slot': 'Side'}
        
        # 2. 없으면 기존 블록의 Main 슬롯(680) 확인
        if not best_placement:
            for opt in orientations:
                for block in blocks:
                    if opt['w'] <= 680 and opt['h'] <= 2384 - block["m_h"]:
                        if best_placement is None or opt['h'] < best_placement['h']:
                            best_placement = {**opt, 'block': block, 'slot': 'Main'}
        
        # 3. 신규 블록 생성 시 높이가 가장 낮은 방향 선택
        if not best_placement:
            # 가능한 옵션 중 높이(h)가 작은 순으로 정렬
            valid_opts = sorted([o for o in orientations if o['w'] <= 1172], key=lambda x: x['h'])
            best_opt = valid_opts[0]
            slot_type = "Main" if best_opt['w'] <= 680 else "Full"
            
            new_block = {"m_h": 0, "s_h": 0, "items": [], "actual_area": 0}
            if slot_type == "Main":
                new_block["m_h"] = best_opt['h']
                new_block["items"].append({"code": code, "x": 0, "y": 0, "w": best_opt['w'], "h": best_opt['h'], "type": "Main"})
            else:
                new_block["m_h"] = new_block["s_h"] = best_opt['h']
                new_block["items"].append({"code": code, "x": 0, "y": 0, "w": best_opt['w'], "h": best_opt['h'], "type": "Full"})
            
            new_block["actual_area"] += (info['w'] * info['d'])
            blocks.append(new_block)
        else:
            # 찾은 최적 위치에 배치
            b = best_placement['block']
            if best_placement['slot'] == 'Side':
                b["items"].append({"code": code, "x": 680, "y": b["s_h"], "w": best_placement['w'], "h": best_placement['h'], "type": "Side"})
                b["s_h"] += best_placement['h']
            else:
                b["items"].append({"code": code, "x": 0, "y": b["m_h"], "w": best_placement['w'], "h": best_placement['h'], "type": "Main"})
                b["m_h"] += best_placement['h']
            b["actual_area"] += (info['w'] * info['d'])
            
    return blocks

# 5. 시각화 (W*D*H 표기 및 자동 회전 텍스트)
def draw_master_plan(ax, block_data, idx):
    total_w, total_h = 1172, 2384
    ax.set_xlim(-250, 1400); ax.set_ylim(-200, 2800)
    
    # 외곽 치수 가이드
    ax.annotate('', xy=(0, 2450), xytext=(1172, 2450), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(586, 2520, f"W {total_w}", ha='center', fontsize=11, fontweight='bold')
    ax.annotate('', xy=(-120, 0), xytext=(-120, 2384), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(-180, 1192, f"H {total_h}", va='center', rotation=90, fontsize=11, fontweight='bold')

    # 구역 배경 및 빨간 점선
    ax.add_patch(patches.Rectangle((0, 0), 680, 2384, facecolor='#F8F9FA', edgecolor='black', alpha=0.3, linestyle=':'))
    ax.add_patch(patches.Rectangle((680, 0), 492, 2384, facecolor='#FFFBF0', edgecolor='black', alpha=0.3, linestyle=':'))
    if not any(item['w'] > 680 for item in block_data["items"]):
        ax.axvline(x=680, color='red', linestyle='--', linewidth=1.5)

    for item in block_data["items"]:
        info = ITEM_MASTER[item['code']]
        ax.add_patch(patches.Rectangle((item['x']+2, item['y']+2), item['w']-4, item['h']-4, facecolor=info['color'], edgecolor='black', linewidth=1.5))
        # 텍스트 회전: 높이가 너비보다 길면 90도 회전하여 가독성 확보
        text_rot = 90 if item['h'] > item['w'] else 0
        label = f"[{item['code']}] {info['name']}\n{info['w']} x {info['d']} x {info['t']}\n({info['unit']}개 생산)"
        ax.text(item['x'] + item['w']/2, item['y'] + item['h']/2, label, ha='center', va='center', fontsize=9, fontweight='heavy', rotation=text_rot)

    yield_val = (block_data["actual_area"] / (total_w * total_h)) * 100
    ax.set_title(f"Block #{idx+1} (수율: {yield_val:.1f}%)", fontsize=15, fontweight='bold', pad=15)
    ax.axis('off')

# 6. 대시보드 출력
planned = plan_optimized_blocks(input_slots)
if planned:
    active_items_count = sum(1 for count in input_slots.values() if count > 0)
    avg_yield = sum((b['actual_area'] / (1172 * 2384)) * 100 for b in planned) / len(planned)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("총 투입 블록", f"{len(planned)} 개")
    col2.metric("생산 품목수", f"{active_items_count} 종")
    col3.metric("평균 수율", f"{avg_yield:.1f} %")
    
    st.divider()
    for row_idx in range(math.ceil(len(planned) / 3)):
        cols = st.columns(3)
        for col_idx in range(3):
            idx = row_idx * 3 + col_idx
            if idx < len(planned):
                with cols[col_idx]:
                    fig, ax = plt.subplots(figsize=(5, 8.5))
                    draw_master_plan(ax, planned[idx], idx)
                    st.pyplot(fig)
else:
    st.info("👈 왼쪽 사이드바에 수량을 입력하면 계산이 시작됩니다.\n\n☎️문의: 생산팀 조상원")
st.write("---")
st.caption("🚀 **Developed by Josangwon** | 📊 *Data-Driven Optimization for iloom*")