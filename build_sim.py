import pandas as pd
import networkx as nx
import os
import json
import random
from tqdm import tqdm

print("[Sim] Starting stability exercise data extraction...")

# --- 1. 路径配置 ---
path = r"d:\shuzirenwendaolun\marvel-project"
template_path = os.path.join(path, "sim.html")
output_path = os.path.join(path, "sim_rendered.html")

# --- 2. 加载基础数据 ---
try:
    # 基础档案（用于获取中文名和排名）
    df_master = pd.read_csv(os.path.join(path, "hero_master_final.csv"))
    # 原始关系网线索
    edges_df = pd.read_csv(os.path.join(path, "cleaned_hero_network.csv"))
except Exception as e:
    print(f"❌ 错误：读取 CSV 失败，请检查文件路径。{e}")
    exit()

# --- 3. 提取核心骨架网络 (Backbone) ---
# 筛选社交影响力最高的前 500 名英雄作为“自选目标池”
# 只有这 500 人的关系会被塞进网页，确保计算速度快且结果具有代表性
top_500 = df_master.sort_values('degree_score', ascending=False).head(500)
top_500_names = set(top_500['English_Name'].tolist())
name_map = dict(zip(top_500['English_Name'], top_500['Chinese_Name']))

# 过滤出这 500 人之间的相互连线
backbone_edges = edges_df[edges_df['hero1'].isin(top_500_names) & edges_df['hero2'].isin(top_500_names)]
G_backbone = nx.from_pandas_edgelist(backbone_edges, 'hero1', 'hero2')

# 将图结构转化为邻接表 (用于 JavaScript 实时计算)
adj_list = {node: list(G_backbone.neighbors(node)) for node in G_backbone.nodes()}
initial_backbone_lcc = len(max(nx.connected_components(G_backbone), key=len))

# --- 4. 预计算“随机湮灭”模式数据 ---
# 核心修改：分母改为 500 (initial_backbone_lcc)，让损毁感与玩家操作量级吻合
random_sim_results = {}

print("[Sim] Simulating random disasters for 500 core heroes...")
for num in tqdm(range(10, 510, 10)): 
    temp_G = G_backbone.copy() # 只在 500 人骨架网中模拟
    all_nodes = list(temp_G.nodes())
    to_remove = random.sample(all_nodes, min(num, len(all_nodes)))
    temp_G.remove_nodes_from(to_remove)
    
    try:
        if temp_G.number_of_nodes() > 0:
            final_size = len(max(nx.connected_components(temp_G), key=len))
            # 损毁率计算：相对于 500 人的比例
            loss_pct = round((initial_backbone_lcc - final_size) / initial_backbone_lcc * 100, 2)
        else:
            loss_pct = 100.0
            final_size = 0
    except:
        loss_pct = 100.0
        final_size = 0
    
    random_sim_results[str(num)] = {
        "loss_pct": loss_pct,
        "msg": f"宇宙遭遇大规模随机消失，约 {num} 名核心领袖化为灰烬。骨架网最大连通群体从 {initial_backbone_lcc} 缩减至 {final_size} 人。"
    }
    
# --- 5. 封装全量数据胶囊 ---
sim_data_capsule = {
    "adj_list": adj_list,               # 500个核心英雄的邻接表
    "hero_names": name_map,             # 英中对照表
    "initial_lcc": initial_backbone_lcc, # 骨架网初始规模
    "random_stats": random_sim_results   # 随机模式预算结果
}

# --- 6. 注入并生成最终网页 ---
print("[Sim] Injecting calculation engine...")
try:
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 注入 JSON 数据
    html_content = html_content.replace('{{ sim_json_data }}', json.dumps(sim_data_capsule, ensure_ascii=False))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("-" * 30)
    print("[OK] Sim system ready!")
    print(f"Please open in browser: {output_path}")
except Exception as e:
    print(f"[ERROR] Injection failed: {e}")