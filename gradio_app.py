import gradio as gr
import os
import time
from pathlib import Path
from copy import deepcopy
from components.blueprints.architect import generate_blueprint, process_blueprint
from components import public_api


'''LOAD ENVIRONMENT VARIABLES'''
from dotenv import load_dotenv
load_dotenv()
NOTION_KEY = os.getenv('NOTION_KEY')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')
MODEL_NAME = os.getenv('MODEL_NAME')
KEYS = {
    'NOTION_KEY': NOTION_KEY,
    'NOTION_PAGE_ID': NOTION_PAGE_ID,
    'UNSPLASH_ACCESS_KEY': UNSPLASH_ACCESS_KEY,
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'MODEL_NAME': MODEL_NAME,
    'HUGGINGFACEHUB_API_TOKEN': HUGGINGFACEHUB_API_TOKEN
    }
VISIBLE_PART = 1/8
VISIBLE_PART_KEYS = {
    _key: _value[:round(len(_value)*VISIBLE_PART)]+'X'*(len(_value)-round(len(_value)*VISIBLE_PART)) for _key, _value in KEYS.items()
    }
ADDITIONAL_INPUTS = [
    ["NOTION_KEY",VISIBLE_PART_KEYS['NOTION_KEY'],'https://www.notion.so/my-integrations'],
    ["NOTION_PAGE_ID",VISIBLE_PART_KEYS['NOTION_PAGE_ID'],"https://www.notion.so/{ACCOUNT_DOMAIN}/{PAGETITLE}-{PAGEID}?"],
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


def private_api(description, llm, model, temperature, top_p, force_json, def_env_var, key_values, auto_restart):
    _auto_restart = False
    try:
        required_keys = list(VISIBLE_KEYS.keys())
        _keys = key_values[key_values['Key'] != '']['Key'].dropna().tolist()
        _values = key_values[key_values['Value'] != '']['Value'].dropna().tolist()
        _keys_with_missing_values = key_values[(key_values['Value'] == '') | (key_values['Value'].isna())]['Key'].dropna().tolist()
        if ((not _keys) or len(_keys) < len(required_keys)) and not def_env_var:
            missing_keys = [_req_k for _req_k in required_keys if _req_k not in _keys]
            yield f"KEY ERROR: {missing_keys} keys are missing in the inputs. Before clicking on the `Run` button, ensure all these Keys '{required_keys}' are in the Key column of the inputs.", """"""
        elif ((not _values) or len(_values) < len(required_keys)) and not def_env_var:
            yield f"VALUE ERROR: {_keys_with_missing_values} keys in the inputs are empty.  Before clicking on the `Run` button, ensure that a valid value is provided in the Value column of the inputs, against all these Keys '{required_keys}'. For detailed instructions to get the value(s), refer to below instructions.", """"""
        else:
            if not def_env_var:
                for _idx, _key in enumerate(key_values['Key'].tolist()):
                    if _key not in required_keys:
                        yield f"KEY ERROR: Given Key '{_key}' is invalid. Valid Keys are {required_keys}.", """"""
                        return
                n = 0
                for _idx, _key in enumerate(key_values['Key'].tolist()):
                    _value = key_values.loc[key_values['Key'] == _key]['Value'].values[-1]
                    yield f"Setting variable '{_key}'", """"""
                    if _value not in VISIBLE_PART_KEYS.values():
                        os.environ[_key] = _value
                    else:
                        os.environ[_key] = KEYS[_key]
                    n += 1
                    time.sleep(1)
                    if n > 0 and _idx + 1 == len(key_values['Key'].tolist()):
                        time.sleep(1)
                        yield f"Environment variables are set successfully. 🎉", """"""
            cumulative_content = ""
            _model = model
            if not def_env_var:
                if model and model != '':
                    if model == VISIBLE_PART_KEYS['MODEL_NAME']:
                        _model = KEYS['MODEL_NAME']
                else:
                    yield f"VALUE ERROR: LLM Model can't be empty.", """"""
                    return
            else:
                _model = KEYS['MODEL_NAME']
            for update in generate_blueprint(description, force_json, temperature, top_p, llm, _model, def_env_var):
                if isinstance(update, dict):
                    yield "Blueprint generation complete. Processing blueprint...", """"""
                    # TO-DO: FOR REFERENCE, ADD CUMULATIVE CONTENT & BLUEPRINT AS TEXT INSIDE NOTION DOC
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
            yield from private_api(description, llm, model, temperature, top_p, force_json, def_env_var, key_values, auto_restart)


def main():
    with gr.Blocks(theme="gradio/base") as app:
        with gr.Tabs() as tabs:
            with gr.TabItem("NotionGPT",id=0) as notiongpt:
                gr.Interface(
                    fn=private_api,
                    inputs=[
                        gr.Textbox(label="Describe your Notion page*", value="Generate me a detailed and comprehensive Notion page to plan a marketing campaign for an oral care brand targeted towards millenials in India."),
                        gr.Dropdown(label="Select LLM Client*", choices=['openai'], multiselect=False, allow_custom_value=True, value='openai', type='value'),
                        gr.Dropdown(label="Select/Add LLM Model*", choices=[VISIBLE_PART_KEYS['MODEL_NAME'],'gpt-3.5-turbo'], multiselect=False, allow_custom_value=True, value=VISIBLE_PART_KEYS['MODEL_NAME'], type='value'),
                    ],
                    outputs=[gr.Text(label="Process Output",placeholder="Here, you will see how NotionGPT creates magic.",show_copy_button=True),"html"],
                    title="NotionGPT - NotionAI on Steroids",
                    description=
                        """
                        - Checkout a sample Notion page generated by NotionGPT: [2-Week Vacation Across India](https://www.notion.so/8d447c76a4cf4460aad2f013cd6e57ba).
                        - This application doesn't store any user information. If you are hesitant to add your keys here, reach out to the creator to build your own NotionGPT (refer to Contact Us).""",
                    submit_btn="Run",
                    clear_btn=None,
                    additional_inputs=[
                        gr.Slider(label="Temperature", minimum=0.1, maximum=1.0, step=0.1, value=0.7, info="Make the model more creative."),
                        gr.Slider(label="Top P", minimum=0.1, maximum=1.0, step=0.1, value=0.2, info="Out of box thinking."),
                        gr.Checkbox(label="Force JSON", value=True),
                        gr.Checkbox(label="Use Default Environment Variables", value=True),
                        gr.DataFrame(
                            label="Input the values. Use references or scroll down for step-wise instructions.",
                            headers=["Key","Value","Reference"],
                            datatype=["str","str","str"],
                            value=ADDITIONAL_INPUTS,
                            row_count=(len(ADDITIONAL_INPUTS),'fixed'),
                            col_count=(3,'fixed'),
                            wrap=True
                        ),
                        gr.Checkbox(label="Auto-restart", value=False)
                    ],
                    article=f"""{Path('components/guides/try_now_guide.md').read_text()}"""
                )
                gr.DownloadButton(label="Download Fine-Tuning Data", value="data/finetuning_data_cot_v7.jsonl", variant="primary")
            with gr.TabItem("BYOK: Bring Your Own Keys",id=1) as notiongpt_trial:
                gr.Interface(
                    fn=public_api.public_api,
                    inputs=[
                        gr.Textbox(label="Describe your Notion page*", value="Generate me a detailed and comprehensive Notion page to plan a brand marketing campaign of Notion as an 'all-in-one workspace to manage both personal & professional work' targeted towards Gen X & Millenials in India."),
                        gr.Dropdown(label="Select LLM Client*", choices=['openai'], multiselect=False, allow_custom_value=True, value='openai', type='value', visible=False),
                        gr.Dropdown(label="Select/Add LLM Model*", choices=['gpt-3.5-turbo'], multiselect=False, allow_custom_value=True, type='value', visible=False),
                        gr.DataFrame(
                            label="Input the values*. Use references or scroll down for step-wise instructions.",
                            headers=["Key","Value","Reference"],
                            datatype=["str","str","str"],
                            value=public_api.ADDITIONAL_INPUTS,
                            row_count=(len(public_api.ADDITIONAL_INPUTS),'fixed'),
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
                gr.DownloadButton(label="Download Fine-Tuning Data", value="data/finetuning_data_cot_v7.jsonl", variant="primary")
            with gr.TabItem("Guide to Build Your Own NotionGPT",id=2) as byongpt_guide:
                gr.Markdown(f"""{Path('components/guides/build_your_own_guide.md').read_text()}""")
            with gr.TabItem("Contact Us", id=3) as contact_us:
                gr.Markdown("""# Click [here](https://github.com/disciple0).""")
    app.launch()


if __name__ == "__main__":
    main()
