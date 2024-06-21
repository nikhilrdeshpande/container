import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from deap import base, creator, tools, algorithms
import random
from datetime import datetime

# Function to convert timestamp to human-readable date
def convert_to_date(timestamp):
    try:
        return datetime.strptime(timestamp, '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M')
    except ValueError:
        return timestamp

# Function to parse BAPLIE file
def parse_baplie(file):
    vessel_info = {}
    container_data = []
    port_names = {
        'BEANR': 'Antwerp', 'FRLEH': 'Le Havre'  # Example mapping, extend as needed
    }
    content = file.read().decode('utf-8')
    current_container = {}
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('TDT'):
            elements = line.split('+')
            vessel_info = {
                'Vessel Number': elements[2],
                'Carrier': elements[4],
                'Vessel Name': elements[7].split(':')[-1]
            }
        elif line.startswith('LOC+5'):
            port_code = line.split('+')[2]
            vessel_info['From Port'] = port_names.get(port_code, port_code)
        elif line.startswith('LOC+61'):
            port_code = line.split('+')[2]
            vessel_info['To Port'] = port_names.get(port_code, port_code)
        elif line.startswith('DTM+136'):
            vessel_info['Start Date'] = convert_to_date(line.split(':')[1])
        elif line.startswith('DTM+178'):
            vessel_info['Planned Arrival Date'] = convert_to_date(line.split(':')[1])
        elif line.startswith('EQD'):
            if current_container:
                container_data.append(current_container)
            elements = line.split('+')
            if len(elements) > 3:
                current_container = {'ContainerNumber': elements[2], 'Type': elements[3]}
        elif line.startswith('LOC+147'):
            container_location = line.split('+')[2]
            current_container['Location'] = container_location
        elif line.startswith('MEA+AAE+AET+KGM'):
            elements = line.split('+')
            weight_str = elements[3].split(':')[1].replace("'", "")
            try:
                current_container['Weight'] = float(weight_str) if weight_str else 0
            except ValueError:
                current_container['Weight'] = 0
        elif line.startswith('DIM+13'):
            dimensions = line.split('+')[2].split(':')
            if len(dimensions) >= 4:
                try:
                    current_container['Length'] = float(dimensions[2]) if dimensions[2] else 0
                    current_container['Width'] = float(dimensions[3]) if dimensions[3] else 0
                    current_container['Height'] = float(dimensions[4]) if dimensions[4] else 0
                except ValueError:
                    current_container['Length'] = 0
                    current_container['Width'] = 0
                    current_container['Height'] = 0
    if current_container:
        container_data.append(current_container)
    return vessel_info, pd.DataFrame(container_data)

# Function to parse COPRAR file
def parse_coprar(file):
    data = []
    current_container = {}
    content = file.read().decode('utf-8')
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('EQD'):
            if current_container:
                data.append(current_container)
            elements = line.split('+')
            current_container = {'ContainerNumber': elements[2] if len(elements) > 2 else 'UNKNOWN'}
        elif line.startswith('MEA') and 'KGM' in line:
            elements = line.split('+')
            weight_str = elements[3].split(':')[1].replace("'", "")
            try:
                current_container['Weight'] = float(weight_str) if weight_str else 0
            except ValueError:
                current_container['Weight'] = 0
        elif line.startswith('DIM+13'):
            dimensions = line.split('+')[2].split(':')
            if len(dimensions) >= 4:
                try:
                    current_container['Length'] = float(dimensions[2]) if dimensions[2] else 0
                    current_container['Width'] = float(dimensions[3]) if dimensions[3] else 0
                    current_container['Height'] = float(dimensions[4]) if dimensions[4] else 0
                except ValueError:
                    current_container['Length'] = 0
                    current_container['Width'] = 0
                    current_container['Height'] = 0
    if current_container:
        data.append(current_container)
    return pd.DataFrame(data)

# Function to parse Equipment file
def parse_equipment(file):
    return pd.read_csv(file)

# Map container locations to 3D coordinates
def map_to_3d_coordinates(container_data):
    def extract_coordinate(loc, index):
        try:
            parts = loc.split(':')
            return int(parts[index]) if len(parts) > index else 0
        except:
            return 0

    container_data['X'] = container_data['Location'].apply(lambda loc: extract_coordinate(loc, 0))
    container_data['Y'] = container_data['Location'].apply(lambda loc: extract_coordinate(loc, 1))
    container_data['Z'] = container_data['Location'].apply(lambda loc: extract_coordinate(loc, 2))
    return container_data

# Visualize using Plotly
def visualize_containers_3d(container_data):
    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=container_data['X'],
        y=container_data['Y'],
        z=container_data['Z'],
        mode='markers',
        marker=dict(
            size=5,
            color=container_data['Weight'],  # Set color to weight for visualization
            colorscale='Viridis',
            opacity=0.8
        ),
        text=container_data['ContainerNumber']
    ))

    fig.update_layout(
        title='3D Visualization of Container Positions',
        scene=dict(
            xaxis_title='X Axis',
            yaxis_title='Y Axis',
            zaxis_title='Z Axis'
        )
    )

    return fig

# Genetic algorithm for sequencing
def genetic_algorithm(data):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    
    def eval_sequence(individual):
        total_weight = 0
        total_moves = 0
        weight_distribution = 0
        for idx in individual:
            container = data.iloc[idx]
            total_weight += container['Weight']
            total_moves += container['Length'] * container['Width']
            # Assuming location is in the form 'row,column'
            try:
                location = container['Location'].split(',')
                weight_distribution += abs(int(location[0]) - int(location[1])) * container['Weight']
            except:
                pass  # Skip invalid location formats
        # Combine different aspects into a single fitness value
        return total_weight + total_moves + weight_distribution,

    toolbox = base.Toolbox()
    toolbox.register("indices", random.sample, range(len(data)), len(data))
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("evaluate", eval_sequence)
    
    population = toolbox.population(n=300)
    algorithms.eaSimple(population, toolbox, cxpb=0.5, mutpb=0.2, ngen=40, verbose=False)
    
    best_individual = tools.selBest(population, k=1)[0]
    return best_individual

st.title('Container Discharge Sequencing (CDS) Optimization')

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

        # Button to generate visualization
        if st.button('Generate Visualization'):
            container_details = map_to_3d_coordinates(container_details)
            fig = visualize_containers_3d(container_details)
            st.plotly_chart(fig)
        
        # Button to generate discharge sequence
        if st.button('Generate Discharge Sequence'):
            if 'ContainerNumber' in baplie_data.columns and 'ContainerNumber' in coprar_data.columns:
                combined_data = pd.merge(baplie_data, coprar_data, on='ContainerNumber')
                
                st.write("Combined Data Shape:", combined_data.shape)
                st.write("Combined Data Head:", combined_data.head())

                if 'Weight' not in combined_data.columns:
                    st.error("'Weight' column is missing in the combined data.")
                else:
                    if not combined_data.empty:
                        sequence_indices = genetic_algorithm(combined_data)
                        st.write("Sequence Indices:", sequence_indices)
                        optimized_sequence = combined_data.iloc[sequence_indices]
                        st.write("Optimized Sequence:", optimized_sequence)
                        
                        fig = px.bar(optimized_sequence, x=optimized_sequence.index, y='Weight', title='Optimized Container Discharge Sequence')
                        st.plotly_chart(fig)

                        st.dataframe(optimized_sequence)
                    else:
                        st.error("Combined data is empty after merging. Please check the input files.")
            else:
                st.error("ContainerNumber column is missing in one of the datasets.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.write("Please upload all required files to proceed.")