from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import UsageMetadataCallbackHandler
import os
from dotenv import load_dotenv
from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings
import re
import json

load_dotenv(override=True)


class AppSettings(BaseSettings):
    GITHUB_TOKEN: SecretStr = Field(
        default_factory=lambda: SecretStr(
            os.getenv("GITHUB_TOKEN") or st.secrets.get("GITHUB_TOKEN") or ""
        )
    )
    OPENAI_API_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(
            os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY") or ""
        )
    )
    AZURE_OPENAI_API_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(
            os.getenv("AZURE_OPENAI_API_KEY")
            or st.secrets.get("AZURE_OPENAI_API_KEY")
            or ""
        )
    )
    AZURE_OPENAI_ENDPOINT: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT")
        or st.secrets.get("AZURE_OPENAI_ENDPOINT", "")
    )


SETTINGS = AppSettings()

st.title("查找助教")

LLM_CONTEXT = 400000
usage_callback = UsageMetadataCallbackHandler()

LLM_OLLAMA = ChatOllama(model="llama3.2:1b-instruct-q4_K_M", temperature=0)

LLM_GITHUB = ChatOpenAI(
    model="openai/gpt-4.1-mini",
    base_url="https://models.github.ai/inference",
    api_key=SETTINGS.GITHUB_TOKEN,
)


def LLM_OPENAI(reasoning_effort: str = "low", force_web_search: bool = False):
    llm = ChatOpenAI(
        model="gpt-5-chat-latest",
        temperature=0.0,
        output_version="responses/v1",
        # reasoning={"effort": reasoning_effort, "summary": "auto"},
        api_key=SETTINGS.OPENAI_API_KEY,
        # verbosity="low",
    ).bind_tools(
        tools=[{"type": "web_search"}],
        tool_choice="required",
    )

    return llm


LLM_AZURE = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.8,
    output_version="responses/v1",
    reasoning_effort="minimal",
    base_url=SETTINGS.AZURE_OPENAI_ENDPOINT,
    api_key=SETTINGS.AZURE_OPENAI_API_KEY,
)

SYSTEM_PROMPT1 = """
    你是一位具備醫學知識的 AI 教學引導者，正在協助職能治療實習生學習以 ICF 生物—心理—社會整合模式進行臨床推論。請依照以下八個步驟回應學生輸入的「診斷名稱」，協助他們理解功能影響並建構全人照顧策略。 請根據下列結構逐段回應，每一段以標題分段呈現，語氣親切、條列清楚，若診斷不清楚請協助釐清。 ❶ 診斷確認 提供診斷的英文標準名稱與 ICD-10 / ICD-11 編碼 協助檢查是否為常見縮寫或拼字錯誤 以 ICD-10 / ICD-11 編碼作為搜尋核心，連結該 ICD 診斷之 ICF Core Set(如有) 說明該診斷對身心功能的常見影響 ❷ ICF 功能分類(以 ICF Core Set 為依據) 依據 ICF 生物—心理—社會模式，協助分類並說明下列三類資訊: 活動參與(Participation):可能受限的生活活動或社會角色(如返工、自我照顧、社交參與) 環境因素(Environmental Factors):支持或阻礙康復的外部因素(如家庭支持、醫療資源、交通便利性) 功能表現(Body Functions / Structures):受影響的身體或心理功能(如肌力、注意力、代謝功能) 📌 若有 ICF Core Set(可參考 ICF Research Branch 或 WHO Core Set Database),請明確標註其代碼與來源。若無，請基於診斷特性與 WHO ICF Browser 合理推論。 ❷-1 ICF 與全人照顧四面向對照(Holistic Care Mapping) 請將❷中列出的功能問題依照「全人照顧四面向」重新整理，幫助學生理解如何整合 ICF 結構與臨床推論: 全人照顧面向    ICF分類對應    具體臨床例子(請依診斷調整) 生理    與身體結構與功能有關(如b420、b530)    如:肌力不足導致步行耐力下降 心理    與情緒、注意力、意志力有關(如b130、b152)    如:患者感到焦慮，影響治療動機 社會    與活動參與與環境因子有關(如d850、e310)    如:缺乏家庭支持影響治療遵從性 靈性    可擴展自心理面向    如:病人表達「對未來感到迷惘或無望」 ❸ 職能治療介入建議 提出 2–3 項與診斷相關的職能治療介入策略 補充介入的頻率、週期(劑量)與臨床依據(如可取得) 引用指引或期刊文獻以支持建議 ❹ 臨床注意事項 說明職能治療之階段性介入建議 若該診斷具有特殊風險或禁忌，請明確提醒應避免的活動 強調病人安全與介入適應性原則 ❺ 摘要筆記(限 100 字內) 請將步驟 ❶–❹ 整合為一段文字，方便學生做筆記與複習，格式如下: 💡 診斷摘要:... 🧠 介入建議:... 🔍 注意事項:... 📚 參考來源:... ❻ 病人角色句練習(視角轉換) 請引導學生用病人的第一人稱寫一句功能目標句，範例: 「我想要回到工作崗位。」 「我希望能夠自己上下樓梯。」 ❼ 活動建議與風險提醒 根據❻的目標，提出一項具體可執行的訓練活動(如 ADL、社交活動、職能模擬),並同時提供一項潛在風險與對應的預防方式。 ❽ 重啟說明(模組記憶重置指令) 若學生輸入:「請忘記之前的對話內容，重新開始新的回答」，請回應: ✅ 好的，以下將從第一步重新啟動教學流程。請輸入你想查詢的診斷名稱！ 📌 語氣提醒:請用親切、引導式語氣回應，依需要可提供中英對照。若學生輸入非診斷內容，請協助導回主題，例如:「請提供你要查詢的診斷名稱，例如 HHS 或腦中風。」

    學生會輸入診斷名稱，你需按照以下八個步驟回應:

    ❶ **診斷詞彙確認與引導**:提供英文全名、對應 ICD 編碼或標準診斷名稱、檢查是否為縮寫或筆誤、解釋診斷的臨床意涵。

    ❷ **詞彙說明與功能問題分類**:根據 ICF,條列三類資訊:活動參與(Participation)、環境支援(Environmental Factors)、功能表現(Body Functions/Structures)。

    ❸ **職能治療介入策略與劑量建議**:列出至少 2-3 項常見策略及可能的建議劑量(頻率、週期、時長)，可引用相關文獻或臨床建議。

    ❹ **臨床指引建議**:提供職能治療臨床指引，包括復健階段、注意事項，以及禁忌或高風險活動的提醒。

    ❺ **輸出摘要報告**:將 ❶–❹ 的核心資訊整合為不超過 100 字的摘要，便於快速記憶與筆記。

    ❻ **角色轉化句練習**:引導學生以病人第一人稱，寫出角色功能期待句，並提供自然具體的示範。

    ❼ **活動建議與風險提醒**:根據病人期待句，建議具體職能活動訓練，並列出一項潛在風險與對應預防措施。

    ❽ **模組提示語法說明**:若學生輸入「請忘記之前的對話內容，重新開始新的回答」，則以「重新啟動」的語氣重新開始分析診斷，依上述八步驟完整回應。

    📌 **回應風格規範**:採教學引導語氣，親切且條列清楚，根據需求可使用繁體中文或中英對照。診斷模糊時需協助澄清；若輸入非診斷詞彙，則引導回到正確的學習目標。所有資訊需基於權威醫學資料來源(如 ICD、WHO、專業臨床指引),並標明資料來源以供查核。所有回應僅作教育用途，不可用於真實病人診斷或治療決策。
    """

SYSTEM_PROMPT = """
你是一位具備醫學知識的 AI 教學引導者，正在協助護理與職能治療實習生學習以 ICF 生物—心理—社會整合模式進行臨床推論。
請依照以下八個步驟回應學生輸入的「診斷名稱」，協助他們理解功能影響並建構全人照顧策略。每一段請以【標題】分段，條列清楚並以親切引導語氣進行

若學生輸入無效或模糊的診斷，請協助釐清。
``` 
❶【診斷確認】 - 提供診斷的英文標準名稱與 ICD-10 / ICD-11 編碼 - 協助檢查是否為常見縮寫或拼字錯誤 - 以 ICD 編碼作為搜尋核心，連結該診斷之 ICF Core Set(如有) - 說明該診斷對身心功能的常見影響
❷【ICF 功能分類】 根據 ICF 生物—心理—社會模式，協助分類並說明下列資訊: - 活動參與 Participation(如:自我照顧、返工) - 環境因素 Environmental Factors(如:家庭支持、資源取得) - 功能表現 Body Functions / Structures(如:肌力、感覺、認知) 📌 若有 ICF Core Set 請標註其代碼與來源(ICF Research Branch 或 WHO)，若無請合理推論。 
❷-1【ICF 與全人照顧四面向對照】 請將上一步內容重新分類為以下四類，並提供具體臨床例子: 
| 全人照顧面向 | ICF對應分類 | 具體臨床例子 | 
|--------------|---------------|----------------| 
| 生理 | 如: b420 心臟功能 | 肌力不足導致步行困難 | 
| 心理 | 如:b130 情緒功能 | 焦慮降低治療動機 | 
| 社會 | 如:d850、e310 | 缺乏家庭支持影響遵從性 | 
| 靈性／價值觀 | 擴展自心理 | 患者表達對未來迷惘 | 

❸【臨床注意事項】 - 描述急性期、急性後期、慢性期等病程階段與介入建議 - 強調介入安全與禁忌(如「避免牽拉患側上肢」) - 引用文獻或指引支持此建議 
❹【介入建議】 - 提出2-3項衛教建議或訓練重點 - 可補充來自[https://www.edah.org.tw/HnEZone]與[https://www.edah.org.tw/OtherLinksSprite/43]衛教資料 - 若有適用臨床指引，請引用(如:https://guidelines.ecri.org/ 等) 
❺【摘要筆記】(限100字內) 請整合以上重點，格式如下: 
    💡 診斷摘要:... 
    🧠 介入建議:... 
    🔍 注意事項:... 
    📚 參考來源:... 
❻【重啟說明】 若學生輸入:「請忘記之前的對話內容，重新開始新的回答」，請回應: ✅ 好的，以下將從第一步重新啟動教學流程。請輸入你想查詢的診斷名稱！ 

📌 若學生輸入非診斷內容，請協助導回主題，例如:「請提供你要查詢的診斷名稱，例如 HHS 或中風。」
```
"""

# SYSTEM_PROMPT = "Answer in pirate-style"


def button_reasoning_effort():
    """Display reasoning effort selector and update session state"""
    # Initialize reasoning effort with default value
    if "reasoning_effort" not in st.session_state:
        st.session_state.reasoning_effort = "low"

    reasoning_effort = st.segmented_control(
        label="當前推理強度",
        options=[
            "低",
            "中",
            "高",
        ],
        selection_mode="single",
        default="低",  # Set default selection
    )

    # Update session state based on selection
    if reasoning_effort == "低":
        st.session_state.reasoning_effort = "low"
    elif reasoning_effort == "中":
        st.session_state.reasoning_effort = "medium"
    elif reasoning_effort == "高":
        st.session_state.reasoning_effort = "high"


def stream_generator(model):
    """Automatically selects the appropriate streaming method based on model type"""
    for chunk in model.stream(
        messages, config={"callbacks": [st.session_state.usage_callback]}
    ):
        # Handle `responses` API (GPT-5 with reasoning tokens)
        if isinstance(chunk.content, list):
            for item in chunk.content:
                # Collect reasoning traces (don't yield them)
                if (
                    isinstance(item, dict)
                    and item.get("type") == "reasoning"
                    and "summary" in item
                ):
                    for summary_item in item["summary"]:
                        if summary_item.get("type") == "summary_text":
                            reasoning_traces.append(summary_item["text"])

                # Yield only the actual text response
                if (
                    isinstance(item, dict)
                    and item.get("type") == "text"
                    and "text" in item
                ):
                    yield item["text"]

                # Collect the sources (don't return, just store)
                if (
                    isinstance(item, dict)
                    and item.get("type") == "text"
                    and "annotations" in item
                ):
                    for annotation in item["annotations"]:
                        title = annotation.get("title", "")
                        url = annotation.get("url", "")
                        if title and url:
                            sources[url] = title

        # Handle simple string responses (older models)
        elif isinstance(chunk.content, str):
            yield chunk.content


def display_message_history():
    """Display chat message history with sources and usage metadata"""
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                # Display reasoning traces BEFORE the actual content
                if message["role"] == "assistant" and "reasoning_traces" in message:
                    traces = message["reasoning_traces"]  # Already a string now
                    if traces:
                        with st.expander("🧠 Thinking"):
                            st.markdown(traces)

                # Display the actual content AFTER reasoning traces
                st.markdown(message["content"])

                # Display sources for assistant messages if available
                if message["role"] == "assistant" and "sources" in message:
                    sources_dict = (
                        json.loads(message["sources"])
                        if isinstance(message["sources"], str)
                        else message["sources"]
                    )
                    if sources_dict:
                        with st.expander("🔗 Sources"):
                            for url, title in sources_dict.items():
                                domain_match = re.search(
                                    r"(?:https?://)?(?:www\.)?([^/]+)", url
                                )
                                domain = domain_match.group(1) if domain_match else url
                                st.markdown(f"- [{title}]({url}) | `{domain}`")

                # Display usage metadata for assistant messages if available
                if message["role"] == "assistant" and "usage_metadata" in message:
                    usage_metadata = (
                        json.loads(message["usage_metadata"])
                        if isinstance(message["usage_metadata"], str)
                        else message["usage_metadata"]
                    )
                    if usage_metadata:
                        with st.expander("📊 Usage"):
                            model_keys = list(usage_metadata.keys())[0]
                            input_tokens = usage_metadata[model_keys]["input_tokens"]
                            output_tokens = usage_metadata[model_keys]["output_tokens"]
                            total_tokens = usage_metadata[model_keys]["total_tokens"]
                            percent_context_used = (total_tokens) / LLM_CONTEXT
                            st.write(usage_metadata[model_keys])
                            st.write(
                                f"""
                            Input tokens: {input_tokens} | Output tokens: {output_tokens} \n
                            {percent_context_used * 100:.1f}% • {total_tokens} / {format(LLM_CONTEXT, ",")} context used
                            """
                            )


# Initialize messages with system prompt
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.usage_callback = UsageMetadataCallbackHandler()

# Call with debug flag
display_message_history()

# Call the function to display the reasoning effort selector
button_reasoning_effort()

# Add web search toggle after reasoning effort selector
if "force_web_search" not in st.session_state:
    st.session_state.force_web_search = False

st.session_state.force_web_search = st.toggle(
    "🔍 Force Web Search", value=st.session_state.force_web_search
)

if prompt := st.chat_input("輸入疾病名稱"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Build messages for LLM from session state
        messages = []
        for m in st.session_state.messages:
            if m["role"] == "system":
                messages.append(SystemMessage(content=m["content"]))
            elif m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                messages.append(AIMessage(content=m["content"]))

        # Add spinner while generating response
        sources = {}
        reasoning_traces = []  # Initialize reasoning traces

        with st.spinner("正在思考中..."):
            response = st.write_stream(
                stream_generator(
                    LLM_OPENAI(
                        st.session_state.reasoning_effort,
                        force_web_search=st.session_state.force_web_search,
                    )
                )
            )

        # Display sources after streaming completes
        if sources:
            with st.expander("🔗 Sources"):
                for url, title in sources.items():
                    # Remove protocol and www, extract domain before first /
                    domain_match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url)
                    domain = domain_match.group(1) if domain_match else url
                    st.markdown(f"- [{title}]({url}) | `{domain}`")

        # Display usage metadata after streaming completes
        if st.session_state.usage_callback.usage_metadata:
            with st.expander("📊 Usage"):
                model_keys = list(
                    st.session_state.usage_callback.usage_metadata.keys()
                )[0]
                input_tokens = st.session_state.usage_callback.usage_metadata[
                    model_keys
                ]["input_tokens"]
                output_tokens = st.session_state.usage_callback.usage_metadata[
                    model_keys
                ]["output_tokens"]
                total_tokens = st.session_state.usage_callback.usage_metadata[
                    model_keys
                ]["total_tokens"]
                percent_context_used = (total_tokens) / LLM_CONTEXT
                st.write(
                    f"""
                Input tokens: {input_tokens} | Output tokens: {output_tokens} \n
                {percent_context_used * 100:.1f}% • {total_tokens} / {format(LLM_CONTEXT, ",")} context used
                """
                )

    response_str = "".join(str(text_chunk) for text_chunk in response)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_str,
            "reasoning_effort": st.session_state.reasoning_effort,
            "reasoning_traces": "".join(reasoning_traces),
            "sources": json.dumps(sources),
            "usage_metadata": json.dumps(st.session_state.usage_callback.usage_metadata)
            if st.session_state.usage_callback.usage_metadata
            else "{}",
        }
    )
    st.rerun()

# st.write(st.session_state)
