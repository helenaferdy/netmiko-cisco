from lib.getCustom.device import Routers, TIMESTAMP, ERROR_COMMAND
import csv
import threading
import os
import yaml

TITLE = "getEnvironment"
COMMAND1 = "show environment"
COMMAND2 = "show env all"
HEADERS = ['No','Hostname', 'Site', 'Power Supply', 'Temperature', 'Fan']
TESTBED =  "testbed/device.yaml"
TEMPLATE_NUMBERS = 5
devices = []
success_counter = []

def main():
    read_testbed()
    export_headers()
    i = 1
    threads = []
    for device in devices:
        t = threading.Thread(target=process_device, args=(device, i))
        t.start()
        threads.append(t)
        i += 1

    for t in threads:
        t.join()

    print(f'\n=========> [{len(success_counter)}/{len(devices)}] devices successfully executed\n')

def process_device(device, i):
    parsed = ""
    num_try = 0
    device.command_template = COMMAND1
    device.out_path = f"out/{TITLE}/"
    device.log_path = f"log/{TITLE}.log"
    device.errorlog = f"log/error/{TITLE}-error.log"
    device.create_folder()
    if device.connect(i):
        command = COMMAND1
        output = "Function exception"
        while output == "Function exception" and device.exception_counter < 3:
            output = device.connect_command(command)

        #try other command
        if [c for c in ERROR_COMMAND if c in output]:
            device.logging_error(f"{device.hostname} : Command [{command}] Failed, trying [{COMMAND2}]")
            command = COMMAND2
            output = device.connect_command(command)
        
        #final check output
        if [c for c in ERROR_COMMAND if c in output]:
            device.logging_error(f"{device.hostname} : Output return empty for command [{command}]")
        else:
            while parsed == "" and num_try < TEMPLATE_NUMBERS:
                num_try += 1
                parsed = device.parse(COMMAND1, output, num_try)
        
        #special templates
        if parsed != "":
            if num_try <= 2:
                final = export_csv(parsed, i, device.hostname)
                device.export_data(final)
            else:
                final = export_csv_3(parsed, i, device.hostname)
                device.export_data(final)
            success_counter.append(0)
        else:
            device.logging_error(f"{device.hostname} : Parsing failed after [{num_try}] tries.")

        device.disconnect()

def export_headers():
    outpath = f'out/{TITLE}/'
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    with open(f"{outpath}{COMMAND1}_{TIMESTAMP}.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(HEADERS)

def read_testbed():
    with open(TESTBED) as f:
        device = yaml.safe_load(f)['devices']
        for d in device:
            the_ip = device[d]['connections']['cli']['ip']
            the_protocol = device[d]['connections']['cli']['protocol']
            the_username = device[d]['credentials']['default']['username']
            the_password = device[d]['credentials']['default']['password']
            the_enable = device[d]['credentials']['enable']['password']
            the_ios_os = device[d]['os']

            new_device = Routers(
                d,
                the_ip,
                the_username,
                the_password,
                the_enable,
                the_ios_os,
                the_protocol
            )
            devices.append(new_device)

#universal template
def export_csv(parsed, i, hostname):
    power = "OK"
    temp = "OK"
    fan = "OK"

    for p in parsed:
        if "pwr" in p['sensor']:
            if p['state'] != "Normal":
                power = "NOK"
        elif "fan" in p['sensor']:
            if p['state'] != "Normal":
                temp = "NOK"
        elif "Temp" in p['sensor']:
            if p['state'] != "Normal":
                fan = "NOK"

    final = [i, hostname, "DC", power, fan, temp]
    return final

#template no 3, 4, 5
def export_csv_3(parsed, i, hostname):
    power = "OK"
    temp = "OK"
    fan = "OK"

    for p in parsed:
        if p['temp'] != "":
            temp = p['temp'] 
        if p['fan'] != "":
            fan = p['fan']

    final = [i, hostname, "DC", power, fan, temp]
    return final