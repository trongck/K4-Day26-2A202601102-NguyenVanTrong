"""Minh hoạ FUNCTION CALLING thuần với Google Gemini SDK.

Tool `get_weather` được định nghĩa schema thủ công VÀ thực thi ngay trong
chính file app này. Model chỉ QUYẾT ĐỊNH gọi tool nào; app mới là nơi chạy.

Cách chạy:
    pip install -r ../requirements.txt
    export GEMINI_API_KEY=...
    python weather_function_calling.py
"""

from google import genai
from google.genai import types

client = genai.Client()

MODEL = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
)

# 1. App tự định nghĩa schema của các tools
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(type=types.Type.STRING, description="Tên thành phố")
        },
        required=["city"],
    ),
)

get_forecast_declaration = types.FunctionDeclaration(
    name="get_forecast",
    description="Lấy dự báo thời tiết cho ngày mai hoặc các ngày tới của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(type=types.Type.STRING, description="Tên thành phố"),
            "days": types.Schema(
                type=types.Type.INTEGER,
                description="Số ngày cần dự báo (mặc định là 1 - ngày mai)",
            ),
        },
        required=["city"],
    ),
)

TOOLS = [
    types.Tool(
        function_declarations=[get_weather_declaration, get_forecast_declaration]
    )
]


# 2. App tự thực thi tool (trong thực tế sẽ gọi API thời tiết thật)
def get_weather(city: str) -> str:
    """Trả về thời tiết hiện tại (mock) của *city*."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }
    import json

    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps(
        {"city": city, **mock_data.get(city, default)}, ensure_ascii=False
    )


def get_forecast(city: str, days: int = 1) -> str:
    """Trả về dự báo thời tiết ngày mai / tương lai (mock) của *city*."""
    mock_forecast = {
        "Hà Nội": {
            "thời_gian": "Ngày mai",
            "dự_báo": "trời nhiều mây, chiều tối có mưa rào rải rác",
            "nhiệt_độ": "24°C - 31°C",
            "khả_năng_mưa": "60%",
            "độ_ẩm": "80%",
        },
        "Hồ Chí Minh": {
            "thời_gian": "Ngày mai",
            "dự_báo": "nắng gián đoạn, trưa chiều có dông cục bộ",
            "nhiệt_độ": "26°C - 34°C",
            "khả_năng_mưa": "70%",
            "độ_ẩm": "75%",
        },
        "Đà Nẵng": {
            "thời_gian": "Ngày mai",
            "dự_báo": "ngày nắng nhẹ, đêm không mưa",
            "nhiệt_độ": "25°C - 32°C",
            "khả_năng_mưa": "20%",
            "độ_ẩm": "70%",
        },
    }
    import json

    default = {
        "thời_gian": "Ngày mai",
        "dự_báo": "nắng nhẹ, nhiệt độ mát mẻ",
        "nhiệt_độ": "25°C - 32°C",
        "khả_năng_mưa": "30%",
        "độ_ẩm": "75%",
    }
    return json.dumps(
        {"city": city, "days": days, **mock_forecast.get(city, default)},
        ensure_ascii=False,
    )


# Bảng tra cứu ánh xạ tên hàm với function thực thi trong App
TOOL_DISPATCHER = {
    "get_weather": get_weather,
    "get_forecast": get_forecast,
}


def run(prompt: str) -> str:
    """Gửi *prompt* tới Gemini, tự động xử lý function calling và trả về câu trả lời cuối."""
    import json

    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    # 3. Gọi model — model quyết định có gọi tool hay không
    resp = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=TOOLS,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả trả lại
    while resp.function_calls:
        # Thêm phản hồi của model vào lịch sử hội thoại
        contents.append(resp.candidates[0].content)

        function_responses = []
        for fc in resp.function_calls:
            print(f"  [model yêu cầu] {fc.name}({fc.args})")
            tool_fn = TOOL_DISPATCHER.get(fc.name)
            if tool_fn:
                result = tool_fn(**fc.args)  # <-- app chạy đúng function tương ứng
            else:
                result = json.dumps(
                    {"error": f"Tool '{fc.name}' không được hỗ trợ"}, ensure_ascii=False
                )
            print(f"  [app thực thi]  -> {result}")
            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name, response={"result": result}
                )
            )

        # Gửi kết quả tool trả về cho model
        contents.append(types.Content(role="user", parts=function_responses))
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )

    # 5. Model tổng hợp câu trả lời cuối
    return resp.text


if __name__ == "__main__":
    question = "Dự báo thời tiết ngày mai ở Hà Nội như thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
