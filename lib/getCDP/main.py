from lib.getCustom.device import Routers, TIMESTAMP, ERROR_COMMAND
import csv
import threading
import os
import yaml

TITLE = "getCDP"
COMMAND1 = "show cdp neighbors"
COMMAND2 = "show cdp neighbor"
COMMAND_PLATFORM = "show platform"
HEADERS = ['No', 'Local Hostname', 'Local Interface', 'Local Platform', 'Remote Hostname', 'Remote Interface', 'Remote Platform', 'Capability']
TESTBED =  "testbed/device.yaml"
TEMPLATE_NUMBERS = 1
TEMPLATE_NUMBERS_PLATFORM = 2
devices = []
success_counter = []
fail_counter = []

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

    end_summary()

def process_device(device, i):
    parsed = ""
    platform = ""
    parsed_platform = ""
    num_try = 0
    num_try_p = 0
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
        
        ## GET PLATFORM
        output_platform = device.connect_command(COMMAND_PLATFORM)
        if [c for c in ERROR_COMMAND if c in output_platform]:
            device.logging_error(f"{device.hostname} : Output return empty for command [{COMMAND_PLATFORM}]")
        else:
            while parsed_platform == "" and num_try_p < TEMPLATE_NUMBERS_PLATFORM:
                num_try_p += 1
                parsed_platform = device.parse(COMMAND_PLATFORM, output_platform, num_try_p)
        if parsed_platform != "":
            platform = parsed_platform[0]['chassis']
    

        #special templates
        if parsed != "":
            final = export_csv(parsed, i, device.hostname, platform)
            device.export_data(final, "cdp")
            success_counter.append(0)
        else:
            device.logging_error(f"{device.hostname} : Parsing failed after [{num_try}] tries.")
            fail_counter.append(f'{device.ip} - {device.ios_os} - {device.hostname}')

        device.disconnect()
    else:
        fail_counter.append(f'{device.ip} - {device.ios_os} - {device.hostname}')

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

def end_summary():
    print(f'\n=> Success : [{len(success_counter)}/{len(devices)}]\n')
    if len(fail_counter) > 0:
        print(f'=> Failed  :')
        for idx, fc in enumerate(fail_counter):
            print(f'   {idx+1}. {fc}')
        print('')

    #universal template
def export_csv(parsed, i, hostname, platform):
    finals = []
    for p in parsed:
        local_int = p['local_interface']
        remote_hostname = p['neighbor']
        remote_platform = p['platform']
        remote_int = p['neighbor_interface']
        capability = p['capability']

        final = [i, hostname, local_int, platform, remote_hostname, remote_int, remote_platform, capability]
        finals.append(final)
    return finals
