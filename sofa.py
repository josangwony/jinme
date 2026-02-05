import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import platform
import math

# 1. 환경 설정 및 폰트 유지
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 마스터 데이터 (W, D, T 유지)
ITEM_MASTER = {
    'A': {'name': '케렌시아 1인', 'w': 550, 'd': 480, 't': 70, 'color': '#FFB6C1', 'unit': 9},
    'B': {'name': '케렌시아 3인', 'w': 1650, 'd': 680, 't': 150, 'color': '#ADD8E6', 'unit': 4},
    'C': {'name': '케렌시아 싱글', 'w': 710, 'd': 640, 't': 150, 'color': '#B0C4DE', 'unit': 4},
    'D': {'name': '오토만', 'w': 660, 'd': 580, 't': 150, 'color': '#FFFFE0', 'unit': 4},
    'E': {'name': '카포네 1인', 'w': 480, 'd': 435, 't': 105, 'color': '#FFE4B5', 'unit': 6},
    'F': {'name': '카포네 2인', 'w': 480, 'd': 755, 't': 105, 'color': '#FFDAB9', 'unit': 6},
    'G': {'name': '카포네 공용', 'w': 480, 'd': 375, 't': 105, 'color': '#F5DEB3', 'unit': 6},
    'H': {'name': '코너 뒤 팔걸이', 'w': 790, 'd': 465, 't': 105, 'color': '#E6E6FA', 'unit': 6},
    'I': {'name': '코너 뒤', 'w': 375, 'd': 465, 't': 105, 'color': '#D8BFD8', 'unit': 6},
    'J': {'name': '코너 팔걸이', 'w': 700, 'd': 465, 't': 105, 'color': '#F0E68C', 'unit': 6}
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

# 4. 백필링 로직 (자동 최적 방향 배치 적용)
def plan_optimized_blocks(slots_dict):
    blocks = []
    temp_list = []
    for code, count in slots_dict.items():
        for _ in range(count): temp_list.append(code)
    # 면적 기준 내림차순 정렬 (큰 것부터 배치)
    all_req_slots = sorted(temp_list, key=lambda x: ITEM_MASTER[x]['w'] * ITEM_MASTER[x]['d'], reverse=True)
    
    for code in all_req_slots:
        info = ITEM_MASTER[code]
        
        # [수정 포인트] 자동 최적 방향 결정 로직
        if code == 'B':
             # B는 무조건 긴 쪽(W)을 높이로
             h, w = info['w'], info['d']
        else:
             # 나머지는 긴 변을 높이(h), 짧은 변을 폭(w)으로 자동 회전
             h = max(info['w'], info['d'])
             w = min(info['w'], info['d'])

        product_area = info['w'] * info['d']
        placed = False
        
        for block in blocks:
            # Main 슬롯 배치 시도
            if w <= 680 and h <= 2384 - block["m_h"]:
                block["items"].append({"code": code, "x": 0, "y": block["m_h"], "w": w, "h": h, "type": "Main"})
                block["actual_area"] += product_area; block["m_h"] += h
                placed = True; break
            # Side 슬롯 배치 시도
            elif w <= 492 and h <= 2384 - block["s_h"]:
                block["items"].append({"code": code, "x": 680, "y": block["s_h"], "w": w, "h": h, "type": "Side"})
                block["actual_area"] += product_area; block["s_h"] += h
                placed = True; break
        
        if not placed:
            # 새 블록 생성
            if w <= 680:
                blocks.append({"m_h": h, "s_h": 0, "items": [{"code": code, "x": 0, "y": 0, "w": w, "h": h, "type": "Main"}], "actual_area": product_area})
            else:
                blocks.append({"m_h": h, "s_h": h, "items": [{"code": code, "x": 0, "y": 0, "w": w, "h": h, "type": "Full"}], "actual_area": product_area})
    return blocks

# 5. 시각화
def draw_master_plan(ax, block_data, idx):
    total_w, total_h = 1172, 2384
    ax.set_xlim(-250, 1400); ax.set_ylim(-200, 2800)
    
    # 외곽 치수 표기
    ax.annotate('', xy=(0, 2450), xytext=(1172, 2450), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(586, 2520, f"W {total_w}", ha='center', fontsize=11, fontweight='bold')
    ax.annotate('', xy=(-120, 0), xytext=(-120, 2384), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(-180, 1192, f"H {total_h}", va='center', rotation=90, fontsize=11, fontweight='bold')

    # 구역 배경
    ax.add_patch(patches.Rectangle((0, 0), 680, 2384, facecolor='#F8F9FA', edgecolor='black', alpha=0.3, linestyle=':'))
    ax.add_patch(patches.Rectangle((680, 0), 492, 2384, facecolor='#FFFBF0', edgecolor='black', alpha=0.3, linestyle=':'))

    # 빨간 점선 (와이드 제품 있으면 숨김)
    has_wide_item = any(item['w'] > 680 for item in block_data["items"])
    if not has_wide_item:
        ax.axvline(x=680, color='red', linestyle='--', linewidth=1.5)

    for item in block_data["items"]:
        info = ITEM_MASTER[item['code']]
        ax.add_patch(patches.Rectangle((item['x']+2, item['y']+2), item['w']-4, item['h']-4, facecolor=info['color'], edgecolor='black', linewidth=1.5))
        
        # 텍스트 회전: 배치된 형태가 세로로 길면 텍스트 회전
        text_rot = 90 if item['h'] > item['w'] else 0
        
        label = f"[{item['code']}] {info['name']}\n{info['w']} x {info['d']} x {info['t']}\n({info['unit']}개)"
        ax.text(item['x'] + item['w']/2, item['y'] + item['h']/2, label, ha='center', va='center', fontsize=9, fontweight='heavy', rotation=text_rot)

    # 순수 수율 계산
    yield_val = (block_data["actual_area"] / (total_w * total_h)) * 100
    ax.set_title(f"Block #{idx+1} (수율: {yield_val:.1f}%)", fontsize=13, fontweight='bold', pad=15)
    ax.axis('off')

# 6. 실행 및 대시보드
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