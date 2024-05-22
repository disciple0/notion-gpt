import os
import gradio as gr
from gradio_client import Client
from pathlib import Path
from copy import deepcopy
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Depends, Request
from starlette.config import Config
from fastapi.responses import FileResponse
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from urllib.parse import urlparse, urlunparse
import uvicorn
from dotenv import load_dotenv
load_dotenv()


'''USER AUTHENTICATION'''
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
SESSION_MIDDLEWARE_SECRET_KEY = os.getenv('SESSION_MIDDLEWARE_SECRET_KEY')
APP_URL = os.getenv('APP_URL')
HOMEPAGE_ROUTE = "/"
SESSION_CHECK_REDIRECTION_ROUTE = "/explore"
SIGNIN_ROUTE = "/signin"
GOOGLE_SIGNIN_ROUTE = "/signin_with_google"
APP_ROUTE = "/app"
APP_ALTERNATE_ROUTE = "/app1"
DEMO_ROUTE = "/demo"
LOGOUT_ROUTE = "/logout"

config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_MIDDLEWARE_SECRET_KEY)

# Dependency to get the current user
def get_user(request: Request):
    user = request.session.get('user')
    if user:
        return user['name']
    return None

@app.get(HOMEPAGE_ROUTE)
def index() -> FileResponse:
    return FileResponse(path="components/static/index.html", media_type="text/html")

@app.get(SESSION_CHECK_REDIRECTION_ROUTE)
def public(user: dict = Depends(get_user)):
    if user:
        return RedirectResponse(url=APP_ROUTE)
    else:
        return RedirectResponse(url=SIGNIN_ROUTE)

@app.route(LOGOUT_ROUTE)
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url=SESSION_CHECK_REDIRECTION_ROUTE)

@app.route(GOOGLE_SIGNIN_ROUTE)
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    redirect_uri = urlunparse(urlparse(str(redirect_uri))._replace(scheme='https'))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/auth')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url=SESSION_CHECK_REDIRECTION_ROUTE)
    request.session['user'] = dict(access_token)["userinfo"]
    return RedirectResponse(url=SESSION_CHECK_REDIRECTION_ROUTE)

ADMIN_USER = os.getenv('ADMIN_USERNAME')
ADMIN_PWD = os.getenv('ADMIN_PASSWORD')
# Dependency for signin with username/password
def pwd_auth(username, password):
    if not username or not password or username == '' or password == '':
        return False
    elif username == ADMIN_USER and password == ADMIN_PWD:
        return True
    else:
        return False

def auth_message(request: gr.Request):
    return f"Welcome, {request.username}"

GRADIO_APP_THEME='gradio/base'
with gr.Blocks(
    theme=GRADIO_APP_THEME,
    css=f"""{Path('components/css/signin_css.md').read_text()}""",
    ) as signin_page:
    gr.Markdown("""<br><br/>""")
    gr.Markdown(f"""{Path('components/guides/notiongpt_intro.md').read_text()}""", line_breaks=True)
    gr.Button(
        value="Sign in with Username/Password", 
        link=APP_ALTERNATE_ROUTE, 
        icon='https://cdn-icons-png.flaticon.com/512/811/811701.png', 
        variant='primary',
        scale=0,
        elem_classes='btn',
        )
    gr.Markdown('### OR')
    gr.Button(
        value="Sign in with Google", 
        link=GOOGLE_SIGNIN_ROUTE, 
        icon='https://lh3.googleusercontent.com/COxitqgJr1sJnIDe8-jiKhxDx1FrYbtRHKJ9z_hELisAlapwE9LUPh6fcXIfb5vwpbMl4xl9H9TRFPc5NOO8Sb3VSgIBrfRYvW6cUA', 
        scale=0, 
        elem_classes='btn',
        )
    gr.Markdown("""
                ## 📩 Try NotionGPT? NotionGPT is invite-only. No sign-up, only sign-in.
                ---
                """)
    gr.Markdown(f"""## 📌 No worries! Click [here]({APP_URL}{DEMO_ROUTE}) to try the live demo app.""")
    gr.Markdown("""<br><br/>""")
    gr.Markdown("""### 💌 <span style="color:gray">[Contact Us](https://www.github.com/disciple0) | Built with inspiration from [github repository](https://github.com/s6bhatti/notion-gpt)</span>""")

app = gr.mount_gradio_app(app, signin_page, path=SIGNIN_ROUTE)


'''MAIN APP'''
NOTIONGPT_HF_GRADIO_API=os.getenv('NOTIONGPT_HF_GRADIO_API')
NOTION_KEY = os.getenv('NOTION_KEY')
ADMIN_NOTION_PAGE_ID = os.getenv('ADMIN_NOTION_PAGE_ID')
USERS_NOTION_PAGE_ID = os.getenv('USERS_NOTION_PAGE_ID')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LLM = "openai"
MODEL_NAME = os.getenv('MODEL_NAME')
HF_TOKEN = os.getenv('APP_HF_TOKEN')
KEYS = {
    'NOTION_KEY': NOTION_KEY,
    'NOTION_PAGE_ID': ADMIN_NOTION_PAGE_ID,
    'USERS_NOTION_PAGE_ID': USERS_NOTION_PAGE_ID,
    'UNSPLASH_ACCESS_KEY': UNSPLASH_ACCESS_KEY,
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'MODEL_NAME': MODEL_NAME,
    'HUGGINGFACEHUB_API_TOKEN': HF_TOKEN
    }
VISIBLE_PART = 1/8
VISIBLE_PART_KEYS = {
    _key: _value[:round(len(_value)*VISIBLE_PART)]+'X'*(len(_value)-round(len(_value)*VISIBLE_PART)) for _key, _value in KEYS.items()
    }
ADDITIONAL_INPUTS = [
    ["NOTION_KEY",VISIBLE_PART_KEYS['NOTION_KEY'],'https://www.notion.so/my-integrations'],
    ["NOTION_PAGE_ID",KEYS['USERS_NOTION_PAGE_ID'],"https://www.notion.so/{ACCOUNT_DOMAIN}/{PAGETITLE}-{PAGEID}?"],
    ["UNSPLASH_ACCESS_KEY",VISIBLE_PART_KEYS['UNSPLASH_ACCESS_KEY'],"https://unsplash.com/oauth/applications"],
    ["OPENAI_API_KEY",VISIBLE_PART_KEYS['OPENAI_API_KEY'],"https://platform.openai.com/api-keys"],
    ["MODEL_NAME",VISIBLE_PART_KEYS['MODEL_NAME'],"https://platform.openai.com/finetune"],
    ["HUGGINGFACEHUB_API_TOKEN",VISIBLE_PART_KEYS['HUGGINGFACEHUB_API_TOKEN'],"https://huggingface.co/settings/tokens"]
    ]
VISIBLE_KEYS = deepcopy(VISIBLE_PART_KEYS)
KEYS_NOT_REQUIRED_AS_INPUTS = ['MODEL_NAME']
for _k in KEYS_NOT_REQUIRED_AS_INPUTS:
    VISIBLE_KEYS.pop(_k, None)
ADDITIONAL_INPUTS = [_input for _input in ADDITIONAL_INPUTS if _input[0] not in KEYS_NOT_REQUIRED_AS_INPUTS]

def main_notiongpt_api(
        description:str, notion_page_id: str, 
        key_values:dict = {}, 
        temperature:float = 0.7, top_p:float = 0.2, 
        force_json:bool = True, def_env_var:bool = False, auto_restart:bool = False
        ):
    llm=LLM
    model=MODEL_NAME
    _key_values = key_values.to_dict('split')
    _key_values['headers'] = _key_values['columns']
    _key_values['metadata'] = None
    _key_values.pop('columns',None)
    _key_values.pop('index',None)
    og_app = Client(NOTIONGPT_HF_GRADIO_API,hf_token=HF_TOKEN)
    result = og_app.predict(
        description=description,
        llm=llm,
        model=model,
        temperature=temperature,
        top_p=top_p,
        force_json=force_json,
        def_env_var=def_env_var,
        key_values=_key_values,
        auto_restart=auto_restart,
        api_name="/predict"
    )
    return result[0], result[1]

def greet(request: gr.Request):
    return f"""### 👋, <span style="color:#1d4ed8">{request.username}</span>. Excited to see what we are going to start today."""

with gr.Blocks(
    theme=GRADIO_APP_THEME,
    css=f"""{Path('components/css/app_css.md').read_text()}""",
    ) as main_app:
    with gr.Tabs() as tabs:
        with gr.TabItem("NotionGPT",id=0) as notiongpt:
            gr.Markdown("""<br><br/>""")
            main_app.load(greet, None, gr.Markdown())
            gr.Interface(
                fn=main_notiongpt_api,
                inputs=[
                    gr.Textbox(label="Describe your Notion page*", value="Generate me a detailed and comprehensive Notion page to plan a brand marketing campaign of Notion as an 'all-in-one workspace to manage both personal & professional work' targeted towards Gen X & Millenials in India.", autofocus=True),
                    gr.Dropdown(label="Select/Add Notion Page ID*", choices=[('User-Generated Notion Pages Repository',KEYS['USERS_NOTION_PAGE_ID'])], multiselect=False, type="value", value=KEYS['USERS_NOTION_PAGE_ID'], allow_custom_value=True),
                    gr.DataFrame(
                        label="Input the values*",
                        headers=["Key","Value","Reference"],
                        datatype=["str","str","str"],
                        value=ADDITIONAL_INPUTS,
                        row_count=(len(ADDITIONAL_INPUTS),'fixed'),
                        col_count=(3,'fixed'),
                        wrap=True,
                        visible=False,
                    ),
                ],
                outputs=[gr.Text(label="Output: NotionGPT Status & Page/Template Link",placeholder="Here, you will see how NotionGPT creates magic.",show_copy_button=True),gr.HTML("""<span style="color:gray">Generated page link would be shown here!</span>""")],
                submit_btn="Generate Notion Page/Template",
                clear_btn=None,
                additional_inputs=[
                    gr.Slider(label="Temperature", minimum=0.1, maximum=1.0, step=0.1, value=0.7, info="Make the model more creative."),
                    gr.Slider(label="Top P", minimum=0.1, maximum=1.0, step=0.1, value=0.2, info="Out of box thinking."),
                    gr.Checkbox(label="Force JSON", value=True),
                    gr.Checkbox(label="Use Default Environment Variables", value=False, interactive=False),
                    gr.Checkbox(label="Auto-restart", value=False, interactive=False)
                ],
                article=None,
                allow_flagging='auto',
            )
            gr.Markdown("""<br><br/>""")
        with gr.TabItem("Get Started", id=1) as about_ngpt:
            gr.Markdown("""<br><br/>""")
            gr.Markdown(f"""{Path('components/guides/notiongpt_intro.md').read_text()}""", elem_classes="center_text")
            gr.Markdown(f"""{Path('components/guides/try_now_guide.md').read_text()}""")
            gr.Markdown("""<br><br/>""")
            gr.DownloadButton(label="Download Fine-Tuning Data", value="data/finetuning_data_cot_v7.jsonl", variant="primary", scale=0, elem_classes='center_btn')
            gr.Markdown("""<br><br/>""")
        with gr.TabItem("Guide to Build Your Own NotionGPT", id=2, visible=False) as byongpt_guide:
            gr.Markdown("""<br><br/>""")
            gr.Markdown(f"""{Path('components/guides/build_your_own_guide.md').read_text()}""")
            gr.Markdown("""<br><br/>""")
            gr.DownloadButton(label="Download Fine-Tuning Data", value="data/finetuning_data_cot_v7.jsonl", variant="primary", scale=0, elem_classes='center_btn')
            gr.Markdown("""<br><br/>""")
        with gr.TabItem("Contact Us", id=3) as contact_us:
            gr.Markdown("""<br><br/>""")
            gr.Markdown("""# Reach out to us by clicking [here](https://www.github.com/disciple0).""")
            gr.Markdown("""<br><br/>""")
        with gr.TabItem("LogOut", id=4) as logout:
            gr.Markdown("""<br><br/>""")
            gr.Button("Logout", link=LOGOUT_ROUTE, scale=0, variant='stop', elem_classes='center_btn')
            gr.Markdown("""<br><br/>""")
    gr.Markdown("""<br><br/>""")
    gr.Markdown(f"""
                ### Have a look at what other NotionGPT users are generating: <a href="https://www.notion.so/{KEYS['USERS_NOTION_PAGE_ID']}" target="_blank">User-generated Notion Pages/Templates</a>.
                ---
                """, elem_classes="center_text")
    gr.Markdown("""`Note: We don't store any user information. If you are hesitant to try NotionGPT on your Notion Workspace, reach out to build your own NotionGPT.`""", elem_classes="center_text")
    gr.Markdown("""#### 💌 <span style="color:gray">Built by [Disciple0](https://www.github.com/disciple0) | With inspiration from [github repository](https://github.com/s6bhatti/notion-gpt)</span>""", elem_classes="center_text")
main_app.queue(max_size=5)


'''DEMO APP'''
ADD_INPUTS = [
    ["NOTION_KEY",None,"https://www.notion.so/my-integrations"],
    ["NOTION_PAGE_ID",None,"https://www.notion.so/{ACCOUNT_DOMAIN}/{PAGETITLE}-{PAGEID}?"],
    ["UNSPLASH_ACCESS_KEY",None,"https://unsplash.com/oauth/applications"],
    ["OPENAI_API_KEY",None,"https://platform.openai.com/api-keys"],
    ["MODEL_NAME",None,"https://platform.openai.com/finetune"]
    ]

def public_notiongpt_api(
        description:str = "Generate me a detailed and comprehensive Notion page to plan a marketing campaign for an oral care brand targeted towards millenials in India.", 
        key_values:dict = {}, 
        temperature:float = 0.7, top_p:float = 0.2, 
        force_json:bool = True, def_env_var:bool = False, auto_restart:bool = False
        ):
    llm="openai"
    model="gpt-3.5-turbo"
    def_env_var = False
    auto_restart = False
    _key_values = key_values.to_dict('split')
    _key_values['headers'] = _key_values['columns']
    _key_values['metadata'] = None
    _key_values.pop('columns',None)
    _key_values.pop('index',None)
    og_app = Client(NOTIONGPT_HF_GRADIO_API,hf_token=HF_TOKEN)
    result = og_app.predict(
        description=description,
        llm=llm,
        model=model,
        key_values=_key_values,
        temperature=temperature,
        top_p=top_p,
        force_json=force_json,
        def_env_var=def_env_var,
        auto_restart=auto_restart,
        api_name="/predict_1"
    )
    return result[0], result[1]

def stranger_greet():
    return f"""### 👋, <span style="color:#1d4ed8">Stranger</span>. Excited to see what we are going to start today."""

with gr.Blocks(
    theme=GRADIO_APP_THEME,
    css=f"""{Path('components/css/app_css.md').read_text()}""",
    ) as demo_app:
    with gr.Tabs() as tabs:
        with gr.TabItem("NotionGPT",id=0) as notiongpt:
            gr.Markdown("""<br><br/>""")
            demo_app.load(stranger_greet, None, gr.Markdown())
            gr.Interface(
                fn=public_notiongpt_api,
                inputs=[
                    gr.Textbox(label="Describe your Notion page*", value="Generate me a detailed and comprehensive Notion page to plan a brand marketing campaign of Notion as an 'all-in-one workspace to manage both personal & professional work' targeted towards Gen X & Millenials in India."),
                    gr.DataFrame(
                        label="Input the values*. Use references or scroll down for step-wise instructions.",
                        headers=["Key","Value","Reference"],
                        datatype=["str","str","str"],
                        value=ADD_INPUTS,
                        row_count=(len(ADD_INPUTS),'fixed'),
                        col_count=(3,'fixed'),
                        wrap=True,
                    ),
                ],
                outputs=[gr.Text(label="Output: NotionGPT Status & Page/Template Link",placeholder="Here, you will see how NotionGPT creates magic.",show_copy_button=True),gr.HTML("""<span style="color:gray">Generated page link would be shown here!</span>""")],
                submit_btn="Generate Notion Page/Template",
                clear_btn=None,
                additional_inputs=[
                    gr.Slider(label="Temperature", minimum=0.1, maximum=1.0, step=0.1, value=0.7, info="Make the model more creative."),
                    gr.Slider(label="Top P", minimum=0.1, maximum=1.0, step=0.1, value=0.2, info="Out of box thinking."),
                    gr.Checkbox(label="Force JSON", value=True),
                    gr.Checkbox(label="Use Default Environment Variables", value=False, interactive=False),
                    gr.Checkbox(label="Auto-restart", value=False, interactive=False)
                ],
                article=None,
                allow_flagging='auto',
            )
            gr.Markdown("""<br><br/>""")
            gr.Markdown("""---""")
            gr.Markdown(f"""{Path('components/guides/try_now_guide.md').read_text()}""")
            gr.Markdown("""<br><br/>""")
            gr.DownloadButton(label="Download Fine-Tuning Data", value="data/finetuning_data_cot_v7.jsonl", variant="primary", scale=0, elem_classes='center_btn')
            gr.Markdown("""<br><br/>""")
        with gr.TabItem("About NotionGPT", id=1) as about_ngpt:
            gr.Markdown("""<br><br/>""")
            gr.Markdown(f"""{Path('components/guides/notiongpt_intro.md').read_text()}""", elem_classes="center_text")
            gr.Markdown("""<br><br/>""")
            gr.Button(
                value="Sign in to App", 
                link=SIGNIN_ROUTE, 
                icon='https://cdn-icons-png.flaticon.com/512/811/811701.png', 
                variant='primary',
                scale=0,
                elem_classes='center_btn',
                )
            gr.Markdown('### OR', elem_classes='center_text')
            gr.Button(
                value="Try Demo App", 
                link=DEMO_ROUTE, 
                icon='https://creazilla-store.fra1.digitaloceanspaces.com/icons/7916148/click-icon-md.png', 
                scale=0, 
                elem_classes='center_btn',
                )
            gr.Markdown("""<br><br/>""")
        with gr.TabItem("Contact Us", id=2) as contact_us:
            gr.Markdown("""<br><br/>""")
            gr.Markdown("""# Reach out to us by clicking [here](https://www.github.com/disciple0).""")
            gr.Markdown("""<br><br/>""")
    gr.Markdown("""<br><br/>""")
    gr.Markdown(f"""
                ### Have a look at what other NotionGPT users are generating: <a href="https://www.notion.so/{KEYS['USERS_NOTION_PAGE_ID']}" target="_blank">User-generated Notion Pages/Templates</a>.
                ---
                """, elem_classes="center_text")
    gr.Markdown("""`Note: We don't store any user information. If you are hesitant to try NotionGPT on your Notion Workspace, reach out to build your own NotionGPT.`""", elem_classes="center_text")
    gr.Markdown("""#### 💌 <span style="color:gray">Built by [Disciple0](https://www.github.com/disciple0) | With inspiration from [github repository](https://github.com/s6bhatti/notion-gpt)</span>""", elem_classes="center_text")
demo_app.queue(max_size=5)

app = gr.mount_gradio_app(app, main_app, path=APP_ROUTE, auth_dependency=get_user)
app = gr.mount_gradio_app(app, main_app, path=APP_ALTERNATE_ROUTE, auth=pwd_auth, auth_message=auth_message)
app = gr.mount_gradio_app(app, demo_app, path=DEMO_ROUTE)

if __name__ == "__main__":
    # main()
    uvicorn.run(app, host='127.0.0.1', port=8000)
