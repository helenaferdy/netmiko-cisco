from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import os
import csv
import logging, sys
import datetime

CONNECT_RETRY = 2
TIMESTAMP = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
os.environ["NTC_TEMPLATES_DIR"] = "lib/getCustom/templates"

class Routers:
    def __init__(self, hostname, ip, username, password, secret, ios_os, protocol, command1):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
        self.secret = secret
        self.ios_os = ios_os
        if protocol == "ssh":
            self.port = "22"
        elif protocol == "telnet":
            self.port = "23"
        self.command1 = command1
        self.exception_counter = 0
        
        self.out_path = "out/getCRC/"
        self.log_path = "log/getCRC.log"
        self.errorlog_path = "log/error/"
        self.errorlog = self.errorlog_path+"getCRC-error.log"

    def create_folder(self):
        try:
            if not os.path.exists(self.out_path):
                os.makedirs(self.out_path)
            if not os.path.exists(self.errorlog_path):
                os.makedirs(self.errorlog_path)
        except:
            pass

    def logging(self, message, type="info"):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s', 
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler(sys.stdout)
                ])
        logging.getLogger().handlers[1].setLevel(logging.WARNING)

        if type == "error":
            logging.error(message)
        elif type == "warning":
            logging.warning(message)
        else:
            logging.info(message)

    def logging_error(self, message, e=""):
        self.logging(message, "error")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.errorlog, 'a') as f:
            f.write(f'{current_time} [ERROR] {message}\n')
            e_list = str(e).split("\n")
            e_list = [line for line in e_list if line.strip()]
            for line in e_list:
                f.write(f'{current_time} {line} \n')

    def connect(self, i):
        self.i = i
        device = {
            "device_type": "cisco_ios",
            "ip": self.ip,
            "username": self.username,
            "password": self.password,
            "secret": self.secret,
            "conn_timeout": 20,
            "port": self.port
        }
        
        self.logging(f"{self.hostname} : Connecting ")
        retry = 0
        while retry < CONNECT_RETRY:
            if retry > 0:
                logging.warning(f"{self.hostname} : Retrying connection")
            try:
                self.connection = ConnectHandler(**device)
                logging.warning(f"{self.hostname} : Connect success")
                retry = 2
                try:
                    self.connection.enable()
                    logging.info(f"{self.hostname} : Entered enable mode")
                    return True
                except Exception as e:
                    err = (f"{self.hostname} : Failed to enter enable mode")
                    self.logging_error(err, e)
            except Exception as e:
                retry +=1
                err = (f"{self.hostname} : Connect Failed ({retry})")
                self.logging_error(err, e)

    def disconnect(self):
        self.connection.disconnect()
        logging.info(f"{self.hostname} : Disconnected succcessfully")        

    def connect_command(self, command):
        try:
            output = self.connection.send_command(command, read_timeout=15)
            logging.info(f"{self.hostname} : Command '{command}' sent")
            return output
        except Exception as e:
            self.exception_counter += 1
            err = (f"{self.hostname} : [{self.exception_counter}] Exception sending command '{command}'")
            self.logging_error(err, e)
            return "Function exception"

    def parse(self, command, output, num_try):
        try:
            parsed_output = parse_output(platform=self.ios_os, command=f'{command} {num_try}', data=output)
            if parsed_output == []:
                err = (f"{self.hostname} : [{num_try}] Parsing empty for template '{command} {num_try}'")
                self.logging_error(err)
                return ""
            else:
                logging.info(f"{self.hostname} : [{num_try}] Parsing success for template '{command} {num_try}'")
                return parsed_output
        except Exception as e:
            err = (f"{self.hostname} : [{num_try}] Parsing exception for template '{command} {num_try}'")
            self.logging_error(err, e)
            return ""

    def export_data(self, final):
        try:
            with open(f"{self.out_path}{self.command1}_{TIMESTAMP}.csv", mode="a", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(final)
                logging.info(f"{self.hostname} : Export success to {self.out_path}{self.command1}_{TIMESTAMP}.csv")
        except Exception as e:
            err = (f"{self.hostname} : Export failed to {self.out_path}{self.command1}_{TIMESTAMP}.csv")
            self.logging_error(err, e)

    ##ONLY CHANGE FROM HERE FOR DIFFERENT COMMAND
    #universal template
    def export_csv(self, parsed):
        for p in parsed:
            interface = p['interface']
            crc = p['crc']
            in_error = p['input_errors']
            out_error = p['output_errors']

            final = [self.i, self.hostname, interface, crc, in_error, out_error]
            self.export_data(final)

