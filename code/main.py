# ------------------------------------------
# # Python 3.6.9
# 
# Entry point of program. Lynchpin of scripts checking requirements, etc.
# 
# Tiffanie Birrell, 10/23/21
# ------------------------------------------

import datetime
from supporting_files.class_validator import Validator
from supporting_files.class_error import Error
from supporting_files.class_score import Score

from supporting_files.script_bpjson import run_bpjson_script
from supporting_files.script_publickey import run_publickey_script
from supporting_files.script_tls import run_tls_script
from supporting_files.script_block_history import run_block_history_script
from supporting_files.script_performance import run_performance_script
from supporting_files.script_peer_node_responsive import run_peer_node_script
# from supporting_files.script_parse_csv_responses import run_parse_csv_script
from supporting_files.script_process_form_pd import run_process_form_script
from supporting_files.script_print_report import print_report

start = datetime.datetime.now()
err = Error() # declare class for handling errors
err.set_debug_mode(False)

max = Score() # declare class for finding max score

filename = "main" # used for error logging

# dict of Validator classes, one per bv_url
bv_classes_dict = {}

# get public keys and account URLs for all BVs
pub_key_dict, bv_account_dict = run_publickey_script(err)

for account, url in bv_account_dict.items():
    bv_classes_dict[account] = Validator(url)

i = -1 # for limit processing number for testing

# process each BV (i.e., generate score)
for account_name, val in bv_classes_dict.items(): # process all BVs
    # limit processing number for testing
    if err.get_debug_mode(): # if in debug mode
        i += 1
        if i == 5: break
        # if i < 0: continue

    print(f'\n{val.url}/bp.json')

    # run bp.json processing
    run_bpjson_script(val, err, max)
    if val.name == "": val.name = val.url
    
    # save the right public key to the class
    try:
        val.public_key = pub_key_dict[val.name]
        val.score += 1
        val.req_fields_dict["public_key"] = 1
        max.add_score("public_key")
    except KeyError as ex:
        err.write_field_error(val, "public_key", filename, "Issue retrieving public key: " + str(ex))
    
    if bool(val.json_data_dict): # evaluates false if dict is empty
        # run TLS processing
        run_tls_script(val, err)

        # check if peer node is responsive
        run_peer_node_script(val, err)

        # check entire block history is saved
        run_block_history_script(val, err)

    # check CPU performance 
    run_performance_script(val, err)
    max.add_score("cpu_performance")

    # add field to calculation of max score
    max.add_score("tls_status")
    max.add_score("p2p")
    max.add_score("block_history")

# run CSV parsing
# run_parse_csv_script(bv_classes_dict, err, max)
run_process_form_script(bv_classes_dict, err, max)

# generate report; 'j' == json, 'i' == individual reports, 'c' == combined report; (allows multiple)
print_report(bv_classes_dict, err, max, "j")

# if in debug mode, log how long it took to run
if err.get_debug_mode():
    finish = datetime.datetime.now()
    runtime = finish - start
    minutes = int(runtime.total_seconds() / 60)
    seconds = int(runtime.total_seconds() - (minutes*60))

    print(f'\nRuntime: {minutes}:{seconds:02}')
