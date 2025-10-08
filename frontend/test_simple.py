"""
简单的Streamlit测试页面
用于验证Streamlit是否正常安装和运行
"""
import streamlit as st

st.set_page_config(
    page_title="测试页面",
    page_icon="✅",
)

st.title("✅ Streamlit 测试页面")

st.success("如果你能看到这个页面,说明Streamlit已经正确安装!")

st.divider()

st.header("📝 简单测试")

name = st.text_input("输入你的名字")
if name:
    st.write(f"你好, {name}!")

number = st.slider("选择一个数字", 0, 100, 50)
st.write(f"你选择的数字是: {number}")

if st.button("点击测试"):
    st.balloons()
    st.success("按钮工作正常!")

st.divider()

st.info("""
**测试通过后,请运行主应用**:
```bash
streamlit run frontend/app.py
```
或使用启动脚本:
```bash
bash run_web.sh
```
""")
