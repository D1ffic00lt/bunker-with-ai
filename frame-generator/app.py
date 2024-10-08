import io

from flask import Flask, request, send_file, make_response

from generator import Generator

app = Flask(__name__)
gen = Generator(
    template_path="static/frame.png",
    font_path="./static/Montserrat-Bold.ttf",
    title_font_path="./static/Gilroy Extra Bold.otf",
    flag_path="./static/red_flag.png",
    skull_path="./static/red_skull.png"
)


@app.route('/api/v1/get-user-frame', methods=['POST'])
async def get_user_frame():
    data = request.json
    buf = io.BytesIO()
    image = gen.generate(data)
    image.save(buf, format='PNG')
    buf.seek(0)
    # with open("image.png", "wb") as file:
    #     file.write(buf.getvalue())
    return make_response(send_file(buf, as_attachment=True, mimetype='image/png', download_name="frame.png"), 201)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1235)
