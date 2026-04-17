# build_simulation.py
# 读取simulation.html模板，生成simulation_rendered.html渲染页
with open("simulation.html", "r", encoding="utf-8") as f:
    template_content = f.read()

with open("simulation_rendered.html", "w", encoding="utf-8") as f:
    f.write(template_content)

print("✅ 作战模拟舱页面构建完成：simulation_rendered.html")