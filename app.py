import os
import streamlit as st

# Файл аты
FILENAME = "finance.txt"


# 1. Деректерді файлдан жүктеу (Try/Except қолдану)
def load_operations(filename):
    operations = []
    if not os.path.exists(filename):
        return operations

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    parts = line.split(":")
                    if len(parts) == 3:
                        op_type, category, amount = parts
                        operations.append(
                            {
                                "type": op_type,
                                "category": category,
                                "amount": float(amount),
                            }
                        )
    except Exception as e:
        st.error(f"Файлды оқуда қате шықты: {e}")
    return operations


# 2. Операцияларды файлға сақтау
def save_operations(operations, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for op in operations:
                f.write(f"{op['type']}:{op['category']}:{op['amount']}\n")
    except Exception as e:
        st.error(f"Файлды сақтауда қате шықты: {e}")


# 3. Балансты есептеу
def get_balance(operations):
    total_income = sum(
        op["amount"] for op in operations if op["type"] == "income"
    )
    total_expense = sum(
        op["amount"] for op in operations if op["type"] == "expense"
    )
    return total_income, total_expense, total_income - total_expense


# 4. Шығыстарды санаттар бойынша топтау
def get_by_category(operations):
    categories = {}
    for op in operations:
        if op["type"] == "expense":
            cat = op["category"]
            categories[cat] = categories.get(cat, 0) + op["amount"]
    return categories


# --- СТРИМЛИТ ИНТЕРФЕЙСІ ---
st.set_page_config(page_title="Жеке қаржы менеджері", page_icon="💰")
st.title("💰 Жеке қаржы менеджері")
st.write("Кірістер мен шығыстарыңызды бақылауға арналған веб-бағдарлама")

# Сессияны ретке келтіру (деректер жоғалып кетпеуі үшін)
if "operations" not in st.session_state:
    st.session_state.operations = load_operations(FILENAME)

operations = st.session_state.operations

# Ағымдағы қаржылық күйді есептеу
total_income, total_expense, current_balance = get_balance(operations)

# Теріс баланс (минусқа кеткенде) ескерту жасау
if current_balance < 0:
    st.error(
        f"⚠️ ЕСКЕРТУ: Сіздің балансыңыз минусқа кетті! Ағымдағы баланс: {current_balance:,.0f} тг"
    )

# --- ЖОҒАРҒЫ ПАНЕЛЬ (БАРЛЫҚ САТЫЛАР) ---
col1, col2, col3 = st.columns(3)
col1.metric(label="Жалпы Кіріс", value=f"{total_income:,.0f} тг")
col2.metric(label="Жалпы Шығыс", value=f"{total_expense:,.0f} тг")
col3.metric(
    label="Ағымдағы Баланс",
    value=f"{current_balance:,.0f} тг",
    delta=None if current_balance >= 0 else "Минус",
)

st.markdown("---")

# --- ОПЕРАЦИЯ ҚОСУ БӨЛІМІ ---
st.subheader("➕ Жаңа операция қосу")

with st.form("add_op_form", clear_on_submit=True):
    op_type = st.selectbox(
        "Операция түрі",
        ["Кіріс (income)", "Шығыс (expense)"],
        index=0,
        key="op_type",
    )
    category = st.text_input("Санаты (мысалы: Зарплата, Тамақ, Көлік):").strip()
    amount_input = st.text_input("Сомасы (тг):")

    submit_btn = st.form_submit_button("Қосу")

    if submit_btn:
        # Енгізу қателерін тексеру (Валидация)
        if not category:
            st.warning("Санатты толтырыңыз!")
        else:
            try:
                amount = float(amount_input)
                if amount <= 0:
                    st.warning("Сома нөлден үлкен болуы керек!")
                else:
                    # Түрін анықтау
                    final_type = (
                        "income"
                        if "Кіріс" in op_type
                        else "expense"
                    )

                    # Операцияны қосу
                    new_op = {
                        "type": final_type,
                        "category": category,
                        "amount": amount,
                    }
                    st.session_state.operations.append(new_op)

                    # Файлға сақтау
                    save_operations(st.session_state.operations, FILENAME)
                    st.success(
                        f"Табысты қосылды: {category} - {amount:,.0f} тг"
                    )
                    st.rerun()  # Бетті жаңарту
            except ValueError:
                st.error("Қате: Сома тек санмен енгізілуі керек!")

st.markdown("---")

# --- ҚАРЖЫЛЫҚ ЕСЕП (МӘЗІР) ---
st.subheader("📊 Қаржылық есеп беру")

if not operations:
    st.info("Әлі ешқандай операция енгізілген жоқ.")
else:
    tab1, tab2 = st.tabs(["Санаттар талдауы", "Транзакциялар тарихы"])

    with tab1:
        st.markdown("#### Санаттар бойынша шығыстар:")
        expense_cats = get_by_category(operations)

        if not expense_cats:
            st.write("Шығыстар әлі жоқ.")
        else:
            top_category = ""
            max_expense = -1

            for cat, amt in expense_cats.items():
                # Пайыздық үлесті есептеу
                percentage = (amt / total_expense) * 100 if total_expense > 0 else 0
                st.write(f"🔹 **{cat}**: {amt:,.0f} тг ({percentage:.1f}%)")

                # Ең көп шығынды табу
                if amt > max_expense:
                    max_expense = amt
                    top_category = cat

            st.markdown("---")
            st.markdown(
                f"🏆 **Ең көп шығын шыққан санат:** <span style='color:red; font-size:18px; font-weight:bold;'>{top_category} ({max_expense:,.0f} тг)</span>",
                unsafe_allow_html=True,
            )

    with tab2:
        st.markdown("#### Барлық операциялар тізімі (`finance.txt` мазмұны):")
        for idx, op in enumerate(reversed(operations), 1):
            icon = "🟢 Кіріс" if op["type"] == "income" else "🔴 Шығыс"
            st.text(
                f"{idx}. [{icon}] {op['category']}: {op['amount']:,.0f} тг"
            )

    # Деректерді тазалау батырмасы (керек болса)
    if st.button("🗑️ Барлық тарихты өшіру"):
        st.session_state.operations = []
        save_operations([], FILENAME)
        st.success("Барлық деректер өшірілді!")
        st.rerun()