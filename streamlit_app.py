import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None

ROLES = ["Admin", "User1", ]

def login():

    st.header("Log in")
    role = st.selectbox("Choose your role", ROLES)

    if st.button("Log in"):
        st.session_state.role = role
        st.rerun()

def logout():
    st.session_state.role = None
    st.rerun()

role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")

video_script = st.Page(
    "request/video_script.py", title="视频脚本生成器", icon=":material/script:"
)
xiaohongshu_copywriting = st.Page(
    "request/xiaohongshu_copywriting.py", title="爆款小红书文案生成器", icon=":material/list_alt_check:"
)
clone_chatAI = st.Page(
    "request/clone_chatAI.py", title="克隆ChatGPT聊天助手", icon=":material/chat:"
)
clever_pdf_chat = st.Page(
    "request/clever_pdf_chat.py", title="智能PDF问答工具", icon=":material/picture_as_pdf:"
)
csv_assistant = st.Page(
    "request/csv_assistant.py", title="CSV数据分析智能工具", icon=":material/csv:"
)
drf_movie = st.Page(
    "respond/drf_movie.py", title="电影网站", icon=":material/movie:"
)
mycompanyysite = st.Page(
    "respond/mycompanyysite.py", title="企业网站", icon=":material/corporate_fare:"
)
admin_1 = st.Page(
    "admin/admin_1.py",
    title="Admin 1",
    icon=":material/person_add:",
    default=(role == "Admin"),
)

request_pages = [video_script, xiaohongshu_copywriting, clone_chatAI, clever_pdf_chat, csv_assistant]
respond_pages = [drf_movie, mycompanyysite]
account_pages = [admin_1, settings, logout_page, ]

# st.title("AIGC")
st.logo("images/horizontal_blue.png", icon_image="images/icon_blue.png")

page_dict = {}
if st.session_state.role in ["User1", "Admin"]:
    page_dict["AIGC"] = request_pages
if st.session_state.role in ["User1", "Admin"]:
    page_dict["我的网站"] = respond_pages

with st.sidebar:
    st.write(f"You are logged in as {st.session_state.role}.")

if len(page_dict) > 0:
    pg = st.navigation(page_dict | {"Account": account_pages})
else:
    pg = st.navigation([st.Page(login)])

pg.run()