import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

# --- 1. 路径配置 ---
path = r"E:\课程资料\6-大三下\数字人文导论\漫威"
template_path = os.path.join(path, "dashboard.html")
output_path = os.path.join(path, "dashboard_rendered.html")

print("🔄 正在启动数据双轨注入引擎...")

# --- 2. 加载终极数据 ---
df = pd.read_csv(os.path.join(path, "hero_master_final.csv"))

# 分别算出两套排行榜
top_degree = df.sort_values('degree_score', ascending=False)
top_between = df.sort_values('betweenness_score', ascending=False)

# --- 3. 辅助函数：生成冠军 HTML 模块 ---
def generate_champion_html(row, score_col, title_label, desc_text):
    # 优先获取大模型链接，否则用默认 logo
    img_url = row.get('Image_URL', './pic/shield_logo.webp')
    if pd.isna(img_url) or str(img_url).strip() == "": 
        img_url = './pic/shield_logo.webp'
        
    score_val = f"{row[score_col]:.4f}"
    
    return f"""
    <div class="champion-section">
        <div class="champ-portrait">
            <img src="{img_url}" class="champ-img" onerror="this.src='./pic/shield_logo.webp'; this.style.objectFit='contain';">
        </div>
        <div>
            <div class="champ-label">{title_label}</div>
            <h2 style="font-size: 48px; margin: 10px 0;">{row['Chinese_Name']}</h2>
            <p style="font-size: 1.2rem; color: var(--shield-cyan);">
                核心评分: {score_val}
            </p>
            <div class="glass-panel" style="margin-top: 20px; background: rgba(0,0,0,0.2);">
                <strong>情报评估：</strong> {desc_text}
            </div>
        </div>
    </div>
    """

# --- 4. 辅助函数：生成排行榜表格 ---
def generate_table_html(df_top, score_col):
    html = "<table class='rank-table'>"
    html += "<tr><th>排名</th><th>代号</th><th>阵营</th><th>战术风险</th><th>核心评分</th></tr>"
    for i, (_, row) in enumerate(df_top.head(15).iterrows()):
        html += f"<tr><td>#{i+1}</td><td style='font-weight:bold;'>{row['Chinese_Name']}</td><td>{row['Primary_Team']}</td><td style='color:#ff4b4b;'>{row['Risk_Level']}/10</td><td style='color:#00f2ff;'>{row[score_col]:.4f}</td></tr>"
    html += "</table>"
    return html

# ----------------- 执行生成 -----------------
total_heroes = str(len(df))

# 1. 生成名望榜 (Degree) 的冠军和表格
champ_degree_html = generate_champion_html(
    top_degree.iloc[0], 'degree_score', 'TOP STRATEGIC HUB (人脉名望)',
    "该个体在全宇宙社交网络中具有不可逾越的统治地位。作为中心节点，其直接接触的英雄数量全宇宙第一。"
)
table_degree_html = generate_table_html(top_degree, 'degree_score')

# 2. 生成外交榜 (Betweenness) 的冠军和表格
champ_between_html = generate_champion_html(
    top_between.iloc[0], 'betweenness_score', 'TOP DIPLOMAT (外交枢纽)',
    "该个体掌握着跨界沟通的命脉。由于其极高的中介中心性，他是连接互不相识的小团体（如复仇者与X战警）的最关键桥梁。"
)
table_between_html = generate_table_html(top_between, 'betweenness_score')

# 3. 生成图表 (Pie & Bar)
faction_power = df.groupby('Alignment')['degree_score'].sum().reset_index()
fig_aln = px.pie(faction_power, values='degree_score', names='Alignment', hole=0.5,
                 color_discrete_sequence=['#ff4b4b', '#00f2ff', '#ffd700'])
fig_aln.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=30, b=10, l=10, r=10))
alignment_chart_html = pio.to_html(fig_aln, full_html=False, include_plotlyjs='cdn')

power_counts = df['Power_Type'].value_counts().head(5).reset_index()
power_counts.columns = ['Power_Type', 'Count']
fig_pwr = px.bar(power_counts, x='Count', y='Power_Type', orientation='h', color_discrete_sequence=['#00f2ff'])
fig_pwr.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=30, b=10, l=10, r=10))
power_chart_html = pio.to_html(fig_pwr, full_html=False, include_plotlyjs=False)

# --- 数据大注入 ---
with open(template_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('{{ total_heroes }}', total_heroes)
html_content = html_content.replace('{{ champ_degree_html }}', champ_degree_html)
html_content = html_content.replace('{{ champ_between_html }}', champ_between_html)
html_content = html_content.replace('{{ table_degree_html }}', table_degree_html)
html_content = html_content.replace('{{ table_between_html }}', table_between_html)
html_content = html_content.replace('{{ alignment_chart_html }}', alignment_chart_html)
html_content = html_content.replace('{{ power_chart_html }}', power_chart_html)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("-" * 30)
print(f"✅ 势力格局页双轨注入完美完成！")
print(f"请在浏览器中双击打开: {output_path}")