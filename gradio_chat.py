import uuid
import requests
import gradio as gr

CHAT_URL = "http://127.0.0.1:8000/chat"
START_URL = "http://127.0.0.1:8000/start"
CHECKOUT_SUBMIT_URL = "http://127.0.0.1:8000/checkout/submit"


def _append(chat_history, role, content):
    chat_history = chat_history or []
    if content is None:
        content = ""
    chat_history.append({"role": role, "content": content})
    return chat_history


def init_conversation(session_id):
    payload = {"session_id": session_id}
    r = requests.post(START_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    reply = data.get("reply", "")
    history = [{"role": "assistant", "content": reply}]

    ui = data.get("ui") or {}
    show_form = bool(ui.get("show_checkout_form", False))
    form_error = ui.get("form_error") or ""
    should_end = bool(ui.get("should_end", False))

    msg_update = gr.update(value="", interactive=not should_end)
    send_update = gr.update(interactive=not should_end)

    # ✅ IMPORTANTE: el submit solo debe estar activo si el form está visible y no terminó
    submit_update = gr.update(interactive=show_form and (not should_end))

    ended_update = should_end

    return (
        history,
        gr.update(visible=show_form),
        form_error,
        msg_update,
        send_update,
        submit_update,
        ended_update,
    )


def new_conversation():
    new_session_id = str(uuid.uuid4())
    history, form_vis, form_error, msg_update, send_update, submit_update, ended_update = init_conversation(
        new_session_id
    )
    return new_session_id, history, form_vis, form_error, msg_update, send_update, submit_update, ended_update


def send_message(message, chat_history, session_id, ended_state):
    chat_history = chat_history or []

    # ✅ si está vacío, no hagas nada (y no pegues al backend)
    if not (message or "").strip():
        # mantenemos todo igual, solo limpiamos msg
        return (
            gr.update(value=""),
            chat_history,
            gr.update(),  # no tocamos visibilidad del form
            "",           # no tocamos form_error
            gr.update(),  # no tocamos send_btn
            gr.update(),  # no tocamos submit_btn
            ended_state,
        )

    # ✅ HARD STOP: si ya terminó, NO dispares el POST
    if ended_state:
        msg_update = gr.update(value="", interactive=False)
        send_update = gr.update(interactive=False)
        submit_update = gr.update(interactive=False)
        return (
            msg_update,
            chat_history,
            gr.update(visible=False),
            "",
            send_update,
            submit_update,
            True,
        )

    payload = {"session_id": session_id, "message": message}
    r = requests.post(CHAT_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    reply = data.get("reply", "")
    ui = data.get("ui") or {}

    if (message or "").strip():
        chat_history = _append(chat_history, "user", message)
    chat_history = _append(chat_history, "assistant", reply)

    show_form = bool(ui.get("show_checkout_form", False))
    form_error = ui.get("form_error") or ""
    should_end = bool(ui.get("should_end", False))

    msg_update = gr.update(value="", interactive=not should_end)
    send_update = gr.update(interactive=not should_end)
    submit_update = gr.update(interactive=show_form and (not should_end))
    ended_update = should_end

    return (
        msg_update,
        chat_history,
        gr.update(visible=show_form),
        form_error,
        send_update,
        submit_update,
        ended_update,
    )


def submit_checkout_form(session_id, chat_history, full_name, address_line1, city, postal_code, phone, ended_state):
    chat_history = chat_history or []

    # ✅ si ya terminó, no hacemos nada
    if ended_state:
        return (
            chat_history,
            gr.update(visible=False),
            "",
            full_name,
            address_line1,
            city,
            postal_code,
            phone,
            gr.update(value="", interactive=False),
            gr.update(interactive=False),
            gr.update(interactive=False),  # submit_btn
            True,
        )

    payload = {
        "session_id": session_id,
        "full_name": full_name,
        "address_line1": address_line1,
        "city": city,
        "postal_code": postal_code,
        "phone": phone,
    }

    r = requests.post(CHECKOUT_SUBMIT_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    reply = data.get("reply", "")
    ui = data.get("ui") or {}

    chat_history = _append(chat_history, "assistant", reply)

    show_form = bool(ui.get("show_checkout_form", False))
    form_error = ui.get("form_error") or ""
    should_end = bool(ui.get("should_end", False))

    msg_update = gr.update(value="", interactive=not should_end)
    send_update = gr.update(interactive=not should_end)
    submit_update = gr.update(interactive=show_form and (not should_end))
    ended_update = should_end

    # clear inputs on success
    if not show_form and not form_error:
        return (
            chat_history,
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            "",
            "",
            msg_update,
            send_update,
            submit_update,
            ended_update,
        )

    # keep form visible if error
    return (
        chat_history,
        gr.update(visible=show_form),
        form_error,
        full_name,
        address_line1,
        city,
        postal_code,
        phone,
        msg_update,
        send_update,
        submit_update,
        ended_update,
    )


with gr.Blocks(title="Perfume Bot — Gradio Chat") as demo:
    gr.Markdown(
        "## 🧴 Perfume Bot — Gradio Chat\n"
        "Mantiene conversación real usando `session_id`"
    )

    ended_state = gr.State(False)

    session_id = gr.Textbox(label="session_id", value=str(uuid.uuid4()))
    chatbot = gr.Chatbot(label="Chat")
    msg = gr.Textbox(label="Escribe tu mensaje")
    send_btn = gr.Button("Enviar")
    new_btn = gr.Button("Nueva conversación")

    checkout_group = gr.Group(visible=False)
    with checkout_group:
        gr.Markdown("### 📦 Datos de envío / facturación")
        form_error = gr.Markdown("", visible=True)

        full_name = gr.Textbox(label="Nombre completo")
        address_line1 = gr.Textbox(label="Dirección")
        city = gr.Textbox(label="Ciudad")
        postal_code = gr.Textbox(label="Código postal")
        phone = gr.Textbox(label="Teléfono")

        submit_btn = gr.Button("Guardar datos y continuar", interactive=False)

    # ✅ click + ENTER
    send_btn.click(
        send_message,
        inputs=[msg, chatbot, session_id, ended_state],
        outputs=[msg, chatbot, checkout_group, form_error, send_btn, submit_btn, ended_state],
    )
    msg.submit(
        send_message,
        inputs=[msg, chatbot, session_id, ended_state],
        outputs=[msg, chatbot, checkout_group, form_error, send_btn, submit_btn, ended_state],
    )

    submit_btn.click(
        submit_checkout_form,
        inputs=[session_id, chatbot, full_name, address_line1, city, postal_code, phone, ended_state],
        outputs=[
            chatbot,
            checkout_group,
            form_error,
            full_name,
            address_line1,
            city,
            postal_code,
            phone,
            msg,
            send_btn,
            submit_btn,
            ended_state,
        ],
    )

    new_btn.click(
        new_conversation,
        inputs=[],
        outputs=[session_id, chatbot, checkout_group, form_error, msg, send_btn, submit_btn, ended_state],
    )

    demo.load(
        init_conversation,
        inputs=[session_id],
        outputs=[chatbot, checkout_group, form_error, msg, send_btn, submit_btn, ended_state],
    )

demo.launch(show_error=True)
