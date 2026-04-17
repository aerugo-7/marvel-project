import pandas as pd
import networkx as nx
import os
import json

print("[Build] Starting dossier data engine...")

# --- 1. 路径配置 ---
path = r"d:\shuzirenwendaolun\marvel-project"
template_path = os.path.join(path, "dossier.html")
output_path = os.path.join(path, "dossier_rendered.html")

# --- 2. 加载数据 ---
df = pd.read_csv(os.path.join(path, "hero_master_final.csv"))
# 清理 NaN
df = df.fillna("--")

with open(os.path.join(path, "neighborhood_index.json"), "r", encoding='utf-8') as f:
    neighbor_idx = json.load(f)

edges_df = pd.read_csv(os.path.join(path, "cleaned_hero_network.csv"))
G_full = nx.from_pandas_edgelist(edges_df, 'hero1', 'hero2')

# 构建名字互相转换的字典
eng_to_cn = dict(zip(df['English_Name'], df['Chinese_Name']))

# --- 3. 生成下拉框选项 HTML ---
hero_list_cn = df['Chinese_Name'].tolist()
hero_options_html = ""
for name in hero_list_cn:
    hero_options_html += f"<option value='{name}'>{name}</option>\n"

# --- 4. 生成庞大的全量英雄数据胶囊 (JSON) ---
shield_data = {}

for _, row in df.iterrows():
    cn_name = row['Chinese_Name']
    eng_name = row['English_Name']
    
    # 获取图片链接，并标准化路径格式
    img_url = str(row.get('Image_URL', './pic/shield_logo.webp'))
    # 将反斜杠转为正斜杠，确保浏览器能正确解析
    img_url = img_url.replace('\\', '/')
    # 确保路径以 ./ 开头（相对路径）
    if not img_url.startswith('./') and not img_url.startswith('http'):
        img_url = './' + img_url
    
    # 雷达图数据放大处理
    radar = [
        row['degree_score'] * 100,
        row['betweenness_score'] * 500,
        row['Loyalty_Score'] * 100,
        row['Cross_Index'] * 100,
        float(row['Risk_Level']) * 10 if str(row['Risk_Level']).replace('.','',1).isdigit() else 50
    ]
    
    # 提取专属社交圈 (限制 20 人)
    friends_eng = neighbor_idx.get(eng_name, [])[:20]
    sub_nodes_eng = [eng_name] + friends_eng
    sub_G = G_full.subgraph(sub_nodes_eng)
    
    # 构建 Vis.js 所需的网络格式
    net_nodes =[]
    for n in sub_G.nodes():
        is_center = (n == eng_name)
        net_nodes.append({
            "id": n,
            "label": eng_to_cn.get(n, n),
            "color": "#00f2ff" if is_center else "#3b82f6",
            "size": 35 if is_center else 15
        })
        
    net_edges =[]
    for e in sub_G.edges():
        net_edges.append({"from": e[0], "to": e[1]})
    
    # 打包这个英雄的所有信息
    shield_data[cn_name] = {
        "img_url": img_url,
        "team": row['Primary_Team'],
        "risk": str(row['Risk_Level']),
        "gender": row.get('Gender', '--'),
        "power_type": row['Power_Type'],
        "mcu": f"{row.get('MCU_Presence', '--')} (约 {row.get('Movie_Count', '--')}部)",
        "mentor": row.get('Mentor_CN', '--'),
        "detail_power": row['Detailed_Power'],
        "social_style": row.get('Social_Style', '--'),
        "radar_values": radar,
        "net_nodes": net_nodes,
        "net_edges": net_edges
    }

# 转化为 JavaScript 可读的 JSON 字符串
hero_json_data = json.dumps(shield_data, ensure_ascii=False)

# --- 5. 注入 HTML 并保存 ---
with open(template_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('{{ hero_options_html }}', hero_options_html)
html_content = html_content.replace('{{ hero_json_data }}', hero_json_data)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("-" * 30)
print("[OK] Dossier inject completed!")
print(f"Please open in browser: {output_path}")