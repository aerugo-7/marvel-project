import pandas as pd
import networkx as nx
import os
import json
import re
from tqdm import tqdm

# --- 1. 路径配置 ---
path = r"E:\课程资料\6-大三下\数字人文导论\漫威"
# 确保使用我们之前生成的战术数据库
db_path = os.path.join(path, "hero_rpg_data.csv") 
network_path = os.path.join(path, "cleaned_hero_network.csv")
master_path = os.path.join(path, "hero_master_final.csv")
template_path = os.path.join(path, "game.html")
output_path = os.path.join(path, "game_rendered.html")

print("⚡ 正在启动神盾局战术演算系统 (Matrix Engine)...")

# --- 2. 辅助函数：生成图片路径 ---
def get_hero_img_path(eng_name):
    # 将 "IRON MAN/TONY STARK" 转为 "iron_man"
    clean_name = eng_name.split('/')[0].strip().lower().replace(' ', '_')
    clean_name = re.sub(r'[^\w]', '', clean_name)
    return f"./pic/heroes/{clean_name}.jpg"

# --- 3. 加载基础数据 ---
if not os.path.exists(db_path):
    print(f"❌ 错误：找不到文件 {db_path}。")
    exit()

tac_df = pd.read_csv(db_path)
master_df = pd.read_csv(master_path)
edges_df = pd.read_csv(network_path)

# 构建全量社交网络（6000+人）
G_base = nx.from_pandas_edgelist(edges_df, 'hero1', 'hero2')
print("📊 正在扫描宇宙权力现状 (PageRank)...")
base_pagerank = nx.pagerank(G_base, max_iter=50)
name_map = dict(zip(master_df['English_Name'], master_df['Chinese_Name']))

# --- 4. 核心演算逻辑 ---
game_db = {}
print(f"🌪️ 正在推演 {len(tac_df)} 位领袖的战术决策连锁反应...")

for _, row in tqdm(tac_df.iterrows(), total=len(tac_df)):
    hero_eng = row['English_Name']
    hero_cn = row['Chinese_Name']
    
    # 模拟 A/B 两个平行时空
    processed_results = {}
    scenarios = [
        {'id': 'A', 'label': row['Action_A_Label'], 'target': str(row['Action_A_Target']).strip(), 'op': 'remove'},
        {'id': 'B', 'label': row['Action_B_Label'], 'target': str(row['Action_B_Target']).strip(), 'op': 'add'}
    ]
    
    for scene in scenarios:
        G_sim = G_base.copy()
        target = scene['target']
        
        # 修改网络结构
        if scene['op'] == 'remove' and G_sim.has_edge(hero_eng, target):
            G_sim.remove_edge(hero_eng, target)
        elif scene['op'] == 'add':
            G_sim.add_edge(hero_eng, target)
            
        # 1. 计算宇宙凝聚力损毁度
        size_new = len(max(nx.connected_components(G_sim), key=len))
        impact_val = round((6399 - size_new) / 63.99, 4)
        
        # 2. 计算权力大洗牌 (PageRank 变化)
        new_pr = nx.pagerank(G_sim, max_iter=30, tol=1e-04)
        diff = {n: new_pr[n] - base_pagerank.get(n, 0) for n in new_pr if n in base_pagerank}
        if hero_eng in diff: del diff[hero_eng]
        
        winner_eng = max(diff, key=diff.get)
        loser_eng = min(diff, key=diff.get)
        
        processed_results[scene['id']] = {
            "label": scene['label'],
            "impact_pct": impact_val if impact_val > 0.01 else "0.01",
            "winner": name_map.get(winner_eng, winner_eng),
            "loser": name_map.get(loser_eng, loser_eng)
        }

    # 封存档案数据
    game_db[hero_cn] = {
        "name": hero_cn,
        "eng": hero_eng,
        "motto_tags": str(row['Motto_Tags']).split('|'),
        "spec_tags": str(row['Spec_Tags']).split('|'),
        "limit_tags": str(row['Limit_Tags']).split('|'),
        "coords": {"x": float(row['Moral_X']), "y": float(row['Moral_Y'])},
        "context": row['Context'],
        "effects": processed_results,
        "audit_pos": row['Audit_Pos'],
        "audit_neg": row['Audit_Neg'],
        "img": get_hero_img_path(hero_eng) # 自动生成路径
    }

# --- 5. 注入 HTML ---
print("💉 正在向网页注入战术情报数据...")
try:
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 注入 JSON 数据
    html_content = html_content.replace('{{ hero_game_json }}', json.dumps(game_db, ensure_ascii=False))
    
    # 注入一个随机 ID 模拟档案编号
    import random
    html_content = html_content.replace('{{ random_id }}', str(random.randint(10000, 99999)))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("-" * 30)
    print(f"✅ 【回响计划】演算大功告成！")
    print(f"最终交互文件已生成：{output_path}")

except Exception as e:
    print(f"❌ 注入失败: {e}")