from pyvis.network import Network
from libs.NetworkTopology.device import Device
import csv
import os
import re

CDP_PATH = "out/getCDP/"
CURRENT_PATH = "libs/NetworkTopology/"
DEVICE_CSV = CURRENT_PATH+"files/device.csv"
FINAL_HTML = CURRENT_PATH+"files/index.html"

def main():
    cdp_file = get_cdp()
    if cdp_file != "":
        extract_cdp(cdp_file)
        create_topology()

def get_cdp():
    cdp_list = []
    try:
        for root, dirs, files in os.walk(CDP_PATH):
            for file in files:
                if file.startswith('.'):
                    pass
                else:
                    the_cdp = os.path.join(root, file)
                    cdp_final = the_cdp.replace("out/getCDP/", "")
                    cdp_list.append(cdp_final)
    except:
        print("No CDP file found. \nRun the Show CDP Menu first.")
        return ""
    
    if cdp_list == []:
        print("No CDP file found. \nRun the Show CDP Menu first.")
        return ""
    else:
        for idx, file in enumerate(cdp_list):
            print(f"{idx+1}. {file}")

        cdp_input = int(input("Select your input : "))
        cdp_file = cdp_list[cdp_input-1]

        return cdp_file

def extract_cdp(cdp_file):
    columns = ["Local Hostname", "Remote Hostname", "Local Interface"]
    replace = ["\(", ".bankmayapada.", ".primacom."]

    input_file = f"{CDP_PATH}{cdp_file}"
    output_file = DEVICE_CSV

    with open(input_file, 'r') as input_file:
        reader = csv.DictReader(input_file)
        extracted_data = []

        for row in reader:
            source = row[columns[0]]
            target = row[columns[1]]
            for r in replace:
                # source = source.replace(r, "")
                source = re.sub(f'{r}.*','', source)
                # target = target.replace(r, "")
                target = re.sub(f'{r}.*','', target)

            extracted_row = {
                "source": source,
                "target": target,
                "weight": 1,
                "int": row[columns[2]]
            }
            extracted_data.append(extracted_row)

    with open(output_file, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["source", "target", "weight", "int"])
        writer.writeheader()
        writer.writerows(extracted_data)



def create_topology():
    net = Network(height='1000px', width='100%', bgcolor='#222222', font_color='white')
    # net.show_buttons(filter_=['nodes'])

    #open csv
    with open(DEVICE_CSV, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data = [row for row in csv_reader]

    #initialize object
    devices = []
    for d in data:
        new_d = Device(d['source'], d['target'], d['weight'])
        devices.append(new_d)

    #initialize object's neighbor
    for d in data:
        for dd in devices:
            if d['source'] == dd.source:
                new_neighbor = []
                new_neighbor.append(d['int'] + ' -> ')
                new_neighbor.append(d['target'] + '\n')
                dd.add_neighbor(new_neighbor)

    #create node
    for dd in devices:
        net.add_node(dd.source, dd.source, title=dd.source)
        net.add_node(dd.target, dd.target, title=dd.target)
        net.add_edge(dd.source, dd.target, value=dd.weight)

    #add neighbor description
    for node in net.nodes:
        for dd in devices:
            if node['id'] == dd.source and node['title'] == dd.source:
                node['title'] = ""
                for n in dd.neighbor:
                    for nn in n:
                        node['title'] += nn

    net.show(FINAL_HTML)
