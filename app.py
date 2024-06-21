import streamlit as st
import pandas as pd
from parsers import parse_baplie, parse_coprar, parse_equipment
from genetic_algorithm import genetic_algorithm
from visualization import visualize_containers_3d
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components


# Serve static files
def serve_static_file(path):
    with open(path, "rb") as f:
        return f.read()

st.title('Container Discharge Sequencing (CDS) Optimization')

# Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose the app mode", ["Discharge Sequencing", "3D Visualization"])

# Upload input data files
baplie_file = st.file_uploader('Upload BAPLIE file', type=['txt', 'edi'])
coprar_file = st.file_uploader('Upload COPRAR file', type=['txt', 'edi'])
equipment_file = st.file_uploader('Upload Equipment file', type='csv')

if baplie_file and coprar_file and equipment_file:
    try:
        st.write("BAPLIE file uploaded:", baplie_file.name)
        st.write("COPRAR file uploaded:", coprar_file.name)
        st.write("Equipment file uploaded:", equipment_file.name)
        
        vessel_info, baplie_data = parse_baplie(baplie_file)
        coprar_data = parse_coprar(coprar_file)
        equipment_data = parse_equipment(equipment_file)

        # Display vessel information in a table
        st.subheader('Vessel Information')
        vessel_df = pd.DataFrame([vessel_info])
        st.table(vessel_df)
        
        # Display container details
        st.subheader('Container Details')
        container_details = pd.merge(baplie_data, coprar_data, on='ContainerNumber', how='left')
        
        # Combine columns and remove duplicates
        container_details['Weight'] = container_details.apply(lambda row: row['Weight_x'] if pd.notna(row['Weight_x']) else row['Weight_y'], axis=1)
        container_details['Length'] = container_details.apply(lambda row: row['Length_x'] if pd.notna(row['Length_x']) else row['Length_y'], axis=1)
        container_details['Width'] = container_details.apply(lambda row: row['Width_x'] if pd.notna(row['Width_x']) else row['Width_y'], axis=1)
        container_details['Height'] = container_details.apply(lambda row: row['Height_x'] if pd.notna(row['Height_x']) else row['Height_y'], axis=1)
        container_details = container_details[['ContainerNumber', 'Type', 'Weight', 'Length', 'Width', 'Height', 'Location']]
        
        st.dataframe(container_details)
        
        # Navigation and Visualization
        if app_mode == "Discharge Sequencing":
            st.header('Discharge Sequencing Optimization')
            
            if st.button('Generate Discharge Sequence'):
                if 'ContainerNumber' in baplie_data.columns and 'ContainerNumber' in coprar_data.columns:
                    combined_data = pd.merge(baplie_data, coprar_data, on='ContainerNumber')
                    
                    if 'Weight' not in container_details.columns:
                        st.error("'Weight' column is missing in the combined data.")
                    else:
                        if not container_details.empty:
                            sequence_indices = genetic_algorithm(container_details)
                            optimized_sequence = container_details.iloc[sequence_indices]
                            
                            fig = px.bar(optimized_sequence, x=optimized_sequence.index, y='Weight', title='Optimized Container Discharge Sequence')
                            st.plotly_chart(fig)

                            st.dataframe(optimized_sequence)
                            
                            # 3D Visualization for Discharge Sequence
                            fig_3d = go.Figure(data=[go.Scatter3d(
                                z=optimized_sequence.index,
                                y=optimized_sequence['Weight'],
                                x=optimized_sequence['Location'],
                                mode='markers',
                                marker=dict(
                                    size=optimized_sequence['Weight'] / 1000,
                                    color=optimized_sequence['Weight'],
                                    colorscale='Viridis',
                                    opacity=0.8
                                ),
                                text=optimized_sequence['ContainerNumber']
                            )])
                            fig_3d.update_layout(
                                title="3D Visualization of Discharge Sequence",
                                scene=dict(
                                    xaxis_title='Location',
                                    yaxis_title='Weight',
                                    zaxis_title='Index',
                                ),
                                margin=dict(l=0, r=0, b=0, t=40)
                            )
                            st.plotly_chart(fig_3d)
                        else:
                            st.error("Combined data is empty after merging. Please check the input files.")
                else:
                    st.error("ContainerNumber column is missing in one of the datasets.")
        
        elif app_mode == "3D Visualization":
            st.header('3D Visualization of Container Positions')
            
            html = visualize_containers_3d(container_details)
            components.html(html, height=800)
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.write("Please upload all required files to proceed.")