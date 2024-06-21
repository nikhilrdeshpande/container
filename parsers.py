import pandas as pd
from datetime import datetime

def parse_baplie(file):
    vessel_info = {}
    container_data = []
    port_names = {
        'BEANR': 'Antwerp', 'FRLEH': 'Le Havre'  # Example mapping, extend as needed
    }
    content = file.read().decode('utf-8')
    current_container = None  # Set to None initially

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
            print(f"startdate", line.split(':')[1])
            vessel_info['Start Date'] = convert_to_date(line.split(':')[1])
        elif line.startswith('DTM+178'):
            vessel_info['Planned Arrival Date'] = convert_to_date(line.split(':')[1])
        elif line.startswith('EQD'):
            if current_container:
                container_data.append(current_container)
            elements = line.split('+')
            current_container = {'ContainerNumber': elements[2], 'Type': elements[3], 'Weight': 0, 'Length': 0, 'Width': 0, 'Height': 0, 'Location': ''}
        elif line.startswith('LOC+147'):
            container_location = line.split('+')[2]
            if current_container is not None:
                current_container['Location'] = container_location
        elif line.startswith('MEA+AAE+AET+KGM'):
            elements = line.split('+')
            weight_str = elements[3].split(':')[1].replace("'", "")
            if current_container is not None:
                try:
                    current_container['Weight'] = float(weight_str) if weight_str else 0
                except ValueError:
                    current_container['Weight'] = 0
        elif line.startswith('DIM+13'):
            dimensions = line.split('+')[2].split(':')
          
            if len(dimensions) >= 4 and current_container is not None:
                
                try:
                    current_container['Length'] = float(dimensions[2]) if dimensions[2] else 0
                    current_container['Width'] = float(dimensions[3]) if dimensions[3] else 0
                    current_container['Height'] = float(dimensions[4])
                    

                except ValueError:
                    current_container['Length'] = 0
                    current_container['Width'] = 0
                    current_container['Height'] = 0
    if current_container:
        container_data.append(current_container)
    return vessel_info, pd.DataFrame(container_data)

def convert_to_date(timestamp):
    try:
        return datetime.strptime(timestamp, '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M')
    except ValueError:
        return timestamp
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

def parse_equipment(file):
    return pd.read_csv(file)