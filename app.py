# -*- coding: utf-8 -*-
import json
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simulador Piloto UAS – Práctica", page_icon="🛩️", layout="centered")

@st.cache_data
def load_questions(csv_path: str):
    df = pd.read_csv(csv_path)
    # normalize
    records = []
    for _, row in df.iterrows():
        try:
            options = json.loads(row['options']) if isinstance(row['options'], str) else []
        except Exception:
            options = []
        records.append({
            'id': int(row['id']),
            'section': str(row['section']),
            'question': str(row['question']),
            'options': options,
            'correct_index': int(row['correct_index']),
            'source': str(row.get('source', ''))
        })
    return records

QUESTIONS = load_questions('questions_sample.csv')
SECTIONS = sorted(set(q['section'] for q in QUESTIONS))

st.title("🛩️ Simulador de examen – Piloto UAS")
st.caption("Banco de preguntas tomado del documento proporcionado por el usuario. Uso exclusivo de estudio.")

with st.sidebar:
    st.header("Ajustes")
    section = st.selectbox("Sección", SECTIONS)
    # Filtrar disponibles
    available = [q for q in QUESTIONS if q['section'] == section]
    n_default = 5 if len(available) >= 5 else len(available)
    n_questions = st.select_slider("Cantidad de preguntas", options=[5, 10], value=min(10, max(5, n_default)))
    if n_questions > len(available):
        n_questions = len(available)
    mode = st.radio("Modo", ["Examen", "Práctica"], index=0, help="Práctica muestra explicación al responder; Examen acumula puntaje y da resultado final.")
    shuffle_options = st.checkbox("Barajar opciones", value=True)
    st.markdown("---")
    reset = st.button("🔁 Reiniciar cuestionario")

if 'quiz' not in st.session_state or reset:
    # construir nuevo set
    pool = [q for q in QUESTIONS if q['section'] == section]
    random.shuffle(pool)
    quiz = pool[:n_questions]
    st.session_state.quiz = quiz
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.answers = []  # (selected_index, correct_index)

quiz = st.session_state.quiz
idx = st.session_state.index if 'index' in st.session_state else 0
score = st.session_state.score if 'score' in st.session_state else 0

if not quiz:
    st.info("No hay preguntas cargadas para esta sección.")
    st.stop()

q = quiz[idx]

st.subheader(f"Pregunta {idx+1} de {len(quiz)}")
st.write(q['question'])

# preparar opciones (barajadas opcionalmente)
indices = list(range(len(q['options'])))
if shuffle_options:
    random.seed(idx)  # mantener estable por pregunta
    random.shuffle(indices)

shuffled_opts = [q['options'][i] for i in indices]
correct_pos = indices.index(q['correct_index'])

selected = st.radio("Selecciona una opción:", shuffled_opts, index=None)

feedback_placeholder = st.empty()
next_col1, next_col2 = st.columns([1,1])

if next_col1.button("Responder", use_container_width=True, disabled=(selected is None)):
    sel_idx = shuffled_opts.index(selected)
    is_correct = sel_idx == correct_pos
    # actualizar estado si modo examen
    if mode == "Examen":
        st.session_state.answers.append((sel_idx, correct_pos))
        if is_correct:
            st.session_state.score += 1
    # feedback
    if is_correct:
        feedback_placeholder.success("✅ ¡Correcto!")
    else:
        correct_text = shuffled_opts[correct_pos]
        feedback_placeholder.error(f"❌ Incorrecto. Respuesta correcta: **{correct_text}**")
    if q.get('source'):
        st.caption(f"Fuente/Referencia: {q['source']}")

if next_col2.button("Siguiente ➡️", use_container_width=True):
    if st.session_state.index < len(quiz) - 1:
        st.session_state.index += 1
    else:
        # finalizar
        if mode == "Examen":
            total = len(quiz)
            st.success(f"Resultado: {st.session_state.score} / {total} ({100*st.session_state.score/total:.0f}%)")
        else:
            st.info("Fin de la práctica.")

st.markdown("---")
st.caption("Consejo: puedes cambiar de sección y tamaño del cuestionario desde el panel lateral. Las opciones se barajan para cada pregunta.")

