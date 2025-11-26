import streamlit as st
from src.report_generator import build_gri_pdf_report, get_available_years_for_reports
from src.email_sender import send_pdf_via_email

st.title("📄 GRI PDF Report Generator")
st.write("Generate a professional GRI-aligned PDF report for a selected year, covering energy, water, emissions, and waste.")

# Load available years
years = get_available_years_for_reports()
selected_year = st.selectbox("Select reporting year", years)

st.write("### Advanced options")

# Initialize session state for PDF
if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None

# Button: Generate PDF
if st.button("Generate PDF"):
    pdf_buffer = build_gri_pdf_report(selected_year)
    st.session_state.pdf_buffer = pdf_buffer  # store for later
    st.success("Report generated successfully!")

# Show download button ONLY if pdf exists
if st.session_state.pdf_buffer:
    st.download_button(
        "⬇ Download PDF Report",
        data=st.session_state.pdf_buffer.getvalue(),
        file_name=f"GRI_Report_{selected_year}.pdf",
        mime="application/pdf",
    )

    # Email section
    st.subheader("📧 Send Report via Email")
    receiver = st.text_input("Recipient Email")

    if st.button("Send Report via Email"):
        try:
            send_pdf_via_email(
                receiver_email=receiver,
                pdf_bytes=st.session_state.pdf_buffer.getvalue(),
                pdf_name=f"GRI_Report_{selected_year}.pdf",
                year=selected_year
            )
            st.success(f"Report successfully emailed to {receiver}")
        except Exception as e:
            st.error(f"Error sending email: {e}")
