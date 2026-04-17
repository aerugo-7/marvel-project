# build_contact.py
# 读取contact.html模板，生成contact_rendered.html渲染页
with open("contact.html", "r", encoding="utf-8") as f:
    template_content = f.read()

with open("contact_rendered.html", "w", encoding="utf-8") as f:
    f.write(template_content)

print("✅ 联系我们页面构建完成：contact_rendered.html")