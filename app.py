import pandas as pd
import streamlit as st
import altair as alt

def upload_file():
    """Ermöglicht den Upload einer CSV-Datei."""
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file:
        try:
            data = pd.read_csv(uploaded_file)
            st.success("File uploaded successfully!")
            return data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None
    return None

def preview_data(data):
    """Zeigt eine Vorschau der hochgeladenen Daten."""
    if data is not None:
        st.write("Preview of Uploaded Data", data.head())

def prepare_data(data):
    """Prüft und bereitet die Daten für Altair vor."""
    if "timestamp" not in data.columns:
        st.error("The 'timestamp' column is missing.")
        return None

    if "hoehe" not in data.columns:
        st.error("The 'hoehe' column is missing.")
        return None

    # Konvertiere Zeitstempel in Datetime-Format
    try:
        data["timestamp"] = pd.to_datetime(data["timestamp"])
    except Exception as e:
        st.error(f"Error converting 'timestamp' to datetime: {e}")
        return None

    # Sicherstellen, dass die Werte der Spalte `hoehe` numerisch sind
    try:
        data["hoehe"] = pd.to_numeric(data["hoehe"], errors="coerce")
    except Exception as e:
        st.error(f"Error converting 'hoehe' to numeric: {e}")
        return None

    if data["hoehe"].isnull().any():
        st.warning("Some 'hoehe' entries could not be converted to numbers and will be dropped.")
        data = data.dropna(subset=["hoehe"])

    return data

def create_interactive_plot(data, x_start, x_end):
    """Erstellt einen interaktiven Altair-Diagramm mit Rechteck-Auswahl."""
    # Filtere die Daten für den aktuellen Bereich
    filtered_data = data[(data["timestamp"] >= x_start) & (data["timestamp"] <= x_end)]

    # Auswahlmechanismus definieren
    selection = alt.selection_interval(encodings=["x"], name="brush")  # Rechteck-Auswahl

    # Basisdiagramm
    base = alt.Chart(filtered_data).mark_line().encode(
        x=alt.X("timestamp:T", title="Timestamp"),
        y=alt.Y("hoehe:Q", title="Height"),
        tooltip=["timestamp:T", "hoehe:Q"]
    ).add_params(selection)

    # Kombiniere die Plots (ohne zusätzliche Hervorhebung)
    combined_chart = base.properties(
        width=800,
        height=400,
        title=f"Interactive Time Series Plot ({x_start} - {x_end})"
    )

    return combined_chart, selection

def main():
    """Komplette Logik des Labeling-Tools."""
    # Datei-Upload
    data = upload_file()
    preview_data(data)

    if data is not None:
        # Daten vorbereiten
        data = prepare_data(data)
        if data is None:
            return

        # Initialisiere Session-State für x-Achsenbereich
        if "x_start" not in st.session_state:
            st.session_state["x_start"] = data["timestamp"].min().to_pydatetime()
        if "x_end" not in st.session_state:
            st.session_state["x_end"] = (data["timestamp"].min() + pd.Timedelta(hours=2)).to_pydatetime()

        # Slider zur Steuerung des x-Achsenbereichs
        # TODO: ändern, sodass es kein slider ist sondern man einfach im plot 
        # mit der maus draggen kann und sich dadurch die x-achse verschiebt
        # TODO: das auswählen des rechtecks muss dann angepasst werden, 
        # dass man durch bspw. cmd + maus die markierung vornimmt
        min_time = data["timestamp"].min().to_pydatetime()
        max_time = data["timestamp"].max().to_pydatetime()

        # sorgt dafür, dass man am anfang eine range von 2 std sieht
        current_start = st.slider(
            "Select Start Time for 2-Hour Range:",
            min_value=min_time,
            max_value=max_time - pd.Timedelta(hours=2).to_pytimedelta(),
            value=st.session_state["x_start"],
            format="YYYY-MM-DD HH:mm"
        )

        # Aktualisiere Session-State basierend auf dem Slider
        st.session_state["x_start"] = current_start
        st.session_state["x_end"] = current_start + pd.Timedelta(hours=2)

        # Plot erstellen
        x_start = st.session_state["x_start"]
        x_end = st.session_state["x_end"]
        chart, selection = create_interactive_plot(data, x_start, x_end)
        st.altair_chart(chart, use_container_width=True)

        # Hinweis für Benutzer
        st.info("Use the selection tool to select data within the visible range and assign labels directly.")

        # Labels zuweisen
        selected_label = st.selectbox("Select a label for selected data:", ["Normal", "Warning", "Error"])
        if st.button("Assign Label"):
            selected_data = data[(data["timestamp"] >= x_start) & (data["timestamp"] <= x_end)]
            
            # Labels zuweisen
            data.loc[selected_data.index, "Label"] = selected_label
            st.success(f"Assigned label '{selected_label}' to the selected range.")

        # Gelabelte Daten anzeigen und exportieren
        st.subheader("Labeled Data")
        st.write(data)

        st.download_button(
            label="Download Labeled Data as CSV",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="labeled_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
