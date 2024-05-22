import gradio as gr
import os
import time
from pathlib import Path
from components.blueprints.architect import generate_blueprint, process_blueprint
import pandas as pd


'''LOAD ENVIRONMENT VARIABLES'''
from dotenv import load_dotenv
load_dotenv()
NOTION_KEY = os.getenv('NOTION_KEY')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME')
KEYS = {
    'NOTION_KEY': NOTION_KEY,
    'NOTION_PAGE_ID': NOTION_PAGE_ID,
    'UNSPLASH_ACCESS_KEY': UNSPLASH_ACCESS_KEY,
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'MODEL_NAME': MODEL_NAME
    }
ADDITIONAL_INPUTS = [
    ["NOTION_KEY",None,'https://www.notion.so/my-integrations'],
    ["NOTION_PAGE_ID",None,"https://www.notion.so/{ACCOUNT_DOMAIN}/{PAGETITLE}-{PAGEID}?"],
    ["UNSPLASH_ACCESS_KEY",None,"https://unsplash.com/oauth/applications"],
    ["OPENAI_API_KEY",None,"https://platform.openai.com/api-keys"],
    ["MODEL_NAME",None,"https://platform.openai.com/finetune"]
    ]


def public_api(description:str, 
        llm:str, 
        model:str, 
        key_values:pd.DataFrame,
        temperature:float, 
        top_p:float, 
        force_json:bool, 
        def_env_var:bool = False, 
        auto_restart:bool = False):
    _auto_restart = False
    try:
        required_keys = list(KEYS.keys())
        _keys = key_values[key_values['Key'] != '']['Key'].dropna().tolist()
        _values = key_values[key_values['Value'] != '']['Value'].dropna().tolist()
        _keys_with_missing_values = key_values[(key_values['Value'] == '') | (key_values['Value'].isna())]['Key'].dropna().tolist()
        if (not _keys) or len(_keys) < len(required_keys):
            missing_keys = [_req_k for _req_k in required_keys if _req_k not in _keys]
            yield f"KEY ERROR: {missing_keys} keys are missing in the inputs. Before clicking on the `Run` button, ensure all these Keys '{required_keys}' are in the Key column of the inputs.", """"""
        elif (not _values) or len(_values) < len(required_keys):
            yield f"VALUE ERROR: {_keys_with_missing_values} keys in the inputs are empty. Before clicking on the `Run` button, ensure that a valid value is provided in the Value column of the inputs, against all these Keys '{required_keys}'. For detailed instructions to get the value(s), refer to below instructions.", """"""
        else:
            n = 0
            for _idx, _key in enumerate(key_values['Key'].tolist()):
                if _key not in required_keys:
                    yield f"KEY ERROR: Given Key '{_key}' is invalid. Valid Keys are {required_keys}.", """"""
                    return
                _value = key_values.loc[key_values['Key'] == _key]['Value'].values[-1]
                yield f"Setting variable '{_key}'", """"""
                os.environ[_key] = _value
                n += 1
                time.sleep(1)
                if n > 0 and _idx + 1 == len(key_values['Key'].tolist()):
                    time.sleep(1)
                    yield f"Environment variables are set successfully. 🎉", """"""
            cumulative_content = ""
            for update in generate_blueprint(description, force_json, temperature, top_p, llm, os.getenv('MODEL_NAME'), def_env_var):
                if isinstance(update, dict):
                    yield "Blueprint generation complete. Processing blueprint...", """"""
                    _auto_restart = auto_restart
                    if not def_env_var:
                        page_id = process_blueprint(os.getenv('NOTION_PAGE_ID'), update.get('blueprint', {}), def_env_var)
                    else:
                        page_id = process_blueprint(NOTION_PAGE_ID, update.get('blueprint', {}), def_env_var)
                    generated_page_link = 'https://notion.so/'+page_id.replace('-','')
                    yield f"Blueprint successfully processed! 🎉", f"""Click <a href="{generated_page_link}" target="_blank">here</a> to check out the NotionGPT-generated page."""
                else:
                    cumulative_content += update
                    yield cumulative_content, """"""
    except Exception as e:
        yield f"Error encountered: {str(e)}. Ensure that the 'Inputs' are correctly filled. Run again.", """"""
        time.sleep(5)
        if _auto_restart == True:
            yield f"Running again...", """"""
            yield from public_api(description, llm, model, key_values, temperature, top_p, force_json, def_env_var, auto_restart)

gr_interface = gr.Interface(
    theme="gradio/base",
    fn=public_api,
    inputs=[
        gr.Textbox(label="Describe your Notion page*", value="Generate me a detailed and comprehensive Notion page to plan a brand marketing campaign of Notion as an 'all-in-one workspace to manage both personal & professional work' targeted towards Gen X & Millenials in India."),
        gr.Dropdown(label="Select LLM Client*", choices=['openai'], multiselect=False, allow_custom_value=True, value='openai', type='value', visible=False),
        gr.Dropdown(label="Select/Add LLM Model*", choices=['gpt-3.5-turbo'], multiselect=False, allow_custom_value=True, type='value', visible=False),
        gr.DataFrame(
            label="Input the values*. Use references or scroll down for step-wise instructions.",
            headers=["Key","Value","Reference"],
            datatype=["str","str","str"],
            value=ADDITIONAL_INPUTS,
            row_count=(len(ADDITIONAL_INPUTS),'fixed'),
            col_count=(3,'fixed'),
            wrap=True,
        ),
    ],
    outputs=[gr.Text(label="Process Output",placeholder="Here, you will see how NotionGPT creates magic.",show_copy_button=True),"html"],
    title="NotionGPT - NotionAI on Steroids. Try it on your Notion Workspace.",
    description=
        """
        Checkout Sample Notion Page: [2-Week Vacation Across India](https://www.notion.so/8d447c76a4cf4460aad2f013cd6e57ba)
        """,
    submit_btn="Run",
    clear_btn=None,
    additional_inputs=[
        gr.Slider(label="Temperature", minimum=0.1, maximum=1.0, step=0.1, value=0.7, info="Make the model more creative."),
        gr.Slider(label="Top P", minimum=0.1, maximum=1.0, step=0.1, value=0.2, info="Out of box thinking."),
        gr.Checkbox(label="Force JSON", value=True),
        gr.Checkbox(label="Use Default Environment Variables", value=False, interactive=False),
        gr.Checkbox(label="Auto-restart", value=False, interactive=False)
    ],
    article=f"""{Path('components/guides/try_now_guide.md').read_text()}"""
)

if __name__ == "__main__":
    # public_api(description='test',llm='openai',model=MODEL_NAME,
    #      key_values=pd.DataFrame(columns=['Key','Value','Reference']),
    #      temperature=0.7, top_p=0.2, force_json=True)
    gr_interface.launch()
