import pandas as pd
import networkx as nx
import os
import json
import re
from tqdm import tqdm

# --- 1. 路径配置 ---
# 请确保此路径与您电脑实际路径一致
path = r"E:\课程资料\6-大三下\数字人文导论\marvel-project"
db_path = os.path.join(path, "hero_tactical_v3.csv") 
network_path = os.path.join(path, "cleaned_hero_network.csv")
master_path = os.path.join(path, "hero_master_final.csv")
template_path = os.path.join(path, "game.html")
output_path = os.path.join(path, "game_rendered.html")

print("[Game] Starting S.H.I.E.L.D. tactical system (Matrix Engine)...")

# --- 2. 辅助函数：解析 Modules_JSON 供步骤04滑块计算使用 ---
def parse_modules(modules_json_str):
    """保持原样逻辑"""
    default_module = {
        "name": "默认行动",
        "weights": {"order": 0, "cohesion": 0, "trust": 0},
        "target_cn": "无",
        "graph_impact": {"impact_pct": "0.01", "winner": "无", "loser": "无"}
    }
    try:
        modules = json.loads(modules_json_str)
        result = {}
        for key in ["Tech", "Diplomacy", "Force"]:
            if key in modules:
                m = modules[key]
                result[key] = {
                    "name": m.get("name", key),
                    "weights": {
                        "order": m.get("order", 0),
                        "cohesion": m.get("cohesion", 0),
                        "trust": m.get("trust", 0)
                    },
                    "target_cn": m.get("impact_target", "无"),
                    "graph_impact": {"impact_pct": "0.01", "winner": "无", "loser": "无"}
                }
            else:
                result[key] = default_module.copy()
        return result
    except:
        return {"Tech": default_module.copy(), "Diplomacy": default_module.copy(), "Force": default_module.copy()}

# --- 3. 加载基础数据 ---
if not os.path.exists(db_path):
    print(f"[ERROR] File not found: {db_path}.")
    exit()

tac_df = pd.read_csv(db_path)
master_df = pd.read_csv(master_path)
edges_df = pd.read_csv(network_path)

G_base = nx.from_pandas_edgelist(edges_df, 'hero1', 'hero2')
print("[Game] Scanning current power status (PageRank)...")
base_pagerank = nx.pagerank(G_base, max_iter=50)
name_map = dict(zip(master_df['English_Name'], master_df['Chinese_Name']))

# --- 4. 核心演算逻辑 ---
game_db = {}
print(f"[Game] Simulating tactical decisions for {len(tac_df)} heroes...")

for _, row in tqdm(tac_df.iterrows(), total=len(tac_df)):
    hero_eng = row['English_Name']
    hero_cn = row['Chinese_Name']
    
    # ==================== 【核心修改点：图片路径硬编码逻辑】 ====================
    # 完全仿照 dashboard 成功的逻辑：处理截断名并指向本地 heroes 文件夹
    # ==================== 【修改部分开始】 ====================
    # 1. 获取文件夹下所有真实的图片文件名
    try:
        actual_files = os.listdir(os.path.join(path, "pic", "heroes"))
    except:
        actual_files = []

    # 2. 准备匹配：把 CSV 里的名字转为纯字母大写
    clean_target = re.sub(r'[^A-Z0-9]', '', str(hero_eng).upper())
    img_url = "./pic/shield_logo.webp" # 默认占位图

    # 3. 遍历文件夹寻找最匹配的文件
    for f in actual_files:
        if f.lower().endswith('.jpg'):
            # 把文件名也转为纯字母大写进行比对
            clean_f = re.sub(r'[^A-Z0-9]', '', f.upper().replace('.JPG', ''))
            # 逻辑：如果名字完全包含，或者前 15 位对得上（处理截断）
            if clean_target.startswith(clean_f) or clean_f.startswith(clean_target[:15]):
                img_url = f"./pic/heroes/{f}"
                break    
    # 解析 Modules_JSON 字段获取两个行动（保持原逻辑不变）
    processed_results = {}
    try:
        modules_json = json.loads(row['Modules_JSON'])
        action_keys = list(modules_json.keys())[:2]
        for i, key in enumerate(action_keys):
            module = modules_json[key]
            action_label = module.get('name', key)
            impact_target = module.get('impact_target', '')
            op = 'add' if module.get('order', 0) > 0 else 'remove'
            
            G_sim = G_base.copy()
            target = impact_target
            
            if target and G_sim.has_node(hero_eng) and G_sim.has_node(target):
                if op == 'remove' and G_sim.has_edge(hero_eng, target):
                    G_sim.remove_edge(hero_eng, target)
                elif op == 'add':
                    G_sim.add_edge(hero_eng, target)
                    
                size_new = len(max(nx.connected_components(G_sim), key=len))
                impact_val = round((6399 - size_new) / 63.99, 4)
                
                new_pr = nx.pagerank(G_sim, max_iter=30, tol=1e-04)
                diff = {n: new_pr[n] - base_pagerank.get(n, 0) for n in new_pr if n in base_pagerank}
                if hero_eng in diff: del diff[hero_eng]
                
                winner_eng = max(diff, key=diff.get) if diff else hero_eng
                loser_eng = min(diff, key=diff.get) if diff else hero_eng
                
                processed_results[key] = {
                    "label": action_label,
                    "impact_pct": impact_val if impact_val > 0.01 else "0.01",
                    "winner": name_map.get(winner_eng, winner_eng),
                    "loser": name_map.get(loser_eng, loser_eng)
                }
    except Exception as e:
        processed_results = {"Tech": {"label": "科技干预", "impact_pct": "0.01", "winner": "美国队长", "loser": "钢铁侠"}}
    
    # 封存档案数据（确保所有键名如 effects、modules 保持原样）
    game_db[hero_cn] = {
        "name": hero_cn,
        "eng": hero_eng,
        "motto_tags": str(row['Motto']).split('|'),
        "spec_tags": str(row['Spec']).split('|'),
        "limit_tags": str(row['Limit']).split('|'),
        "coords": {"x": float(row['X']), "y": float(row['Y'])},
        "context": row['Scenario'],
        "effects": processed_results,
        "audit_pos": str(row['Evaluation'])[:100] if pd.notna(row['Evaluation']) else "",
        "audit_neg": "",
        "img": img_url,   
        "modules": parse_modules(row['Modules_JSON'])
    }

# --- 5. 注入 HTML ---
print("[Game] Injecting tactical data into HTML...")
try:
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    html_content = html_content.replace('{{ hero_game_json }}', json.dumps(game_db, ensure_ascii=False))
    
    import random
    html_content = html_content.replace('{{ random_id }}', str(random.randint(10000, 99999)))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("-" * 30)
    print(f"[OK] game_rendered.html generated successfully!")

except Exception as e:
    print(f"[ERROR] Injection failed: {e}")