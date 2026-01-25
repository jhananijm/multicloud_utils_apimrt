#!/bin/bash

apigee_components=(zkcs ms router mp qpid pg ldap sso)
declare -A prop
declare -A secret

for comp in apigee_components
do
    array_name="${comp}_inventory"
    eval "declare -A $array_name"
done

action_init(){
    echo "********************************************************************"
    echo "************************ Initialising the Node *********************"
    echo "********************************************************************"
    check_success_flag
    set_port
    set_date $2
    set_uuid $1
    iac get-config -d landscape-config -p credentials.cert_file_prop.private_key > /tmp/ssh-private-key
    cp /tmp/ssh-private-key /tmp/ssh-private-key-ansible
    sudo chmod 600 /tmp/ssh-private-key
    create_directories_on_ansible_node /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1} /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1}/inputs /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1}/outputs /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1}/utils
    copy_files_to_ansible_node ${IAC_PRODUCT_DIR}/components/landscape-config/scripts/*,/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1}/utils ${IAC_COMPONENT_DIR}/scripts/*,/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1} /tmp/ssh-private-key-ansible,/tmp/ssh-private-key
    run_command_on_ansible_node "sudo chmod 700 /tmp/ssh-private-key"
    run_command_on_ansible_node "sudo touch /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${1}/outputs/concourse_check.txt"
    check_state_dir
    install_apimrt_utils
    push_secrets
    copy_inventory_to_ansible_node
    echo "********************************************************************"
    echo "************************ Initialising Completed ********************"
    echo "********************************************************************"
}

set_date(){
    date=$1
}

set_uuid(){
    uuid=$1
}

set_port(){
    case $(get_landscape_type) in
    aws|alibaba)
    ssh_port=2222
    ;;
    azure|gcp)
    ssh_port=22
    ;;
    *)
    echo "Unable to get the landscape type : $(get_landscape_type)"
    exit 1;;
    esac

}

install_apimrt_utils(){
    if [ ${IAC_DEPLOYMENT_NAME} == "inventory-generation" ]
    then
        echo "Installing apimrt utils package on the VM..."
        run_command_on_ansible_node "set -o pipefail && \
            sudo python3 -m pip install -U pip && \
            sudo python3 -m pip install --upgrade --force-reinstall /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/utils/apimrt_utils/dist/apimrt-1.0.0-py3-none-any.whl[\"apim-$(get_landscape_type)\"]"
    fi

    if [[ ${IAC_DEPLOYMENT_NAME} == "silent-config" || ${IAC_DEPLOYMENT_NAME} == "pre-validation" || ${IAC_DEPLOYMENT_NAME} == "post-validation" || ${IAC_ACTION_NAME} == "post-action" || ${IAC_DEPLOYMENT_NAME} == "validation" || ${IAC_DEPLOYMENT_NAME} == "landscape-setup" ]]
    then
        echo "Skipping python virtual env setup for ${IAC_DEPLOYMENT_NAME}"
    else
        if [ ! -e ${LANDSCAPE_ROOT}/state/${IAC_DEPLOYMENT_NAME}/state/pyvenv ]
        then
            setup_python_env
        else
            python_path=$(cat ${LANDSCAPE_ROOT}/state/${IAC_DEPLOYMENT_NAME}/state/pyvenv)
            command="ls ${python_path}"
            ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /tmp/ssh-private-key  concourseci@$(get_ansible_ip) -p ${ssh_port} "${command}"
            if [ $? -eq 0 ];then
                echo "Using existing virtual env ${python_path}"
            else
                setup_python_env
            fi

        fi
    fi

    if [ -z "$python_path" ]; then
        python_path="/home/concourseci/scripts/inventory-generation/venv/bin/python3"
    fi

    echo "Python Virtual env in use :::::::::::: ${python_path}"
}

set_success_flag(){
    build_version=$(get_config_value inputs BUILD_VERSION ${IAC_LANDSCAPE_DIR}/deployments/${IAC_DEPLOYMENT_NAME}/inputs/config.yml)
    patch_version=$(get_config_value inputs PATCH_VERSION ${IAC_LANDSCAPE_DIR}/deployments/${IAC_DEPLOYMENT_NAME}/inputs/config.yml)
    version=${build_version}"-"${patch_version}
    run_command_on_ansible_node "set -o pipefail && \
                mkdir -p /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/outputs/state/${IAC_ACTION_NAME}-${version} && \
                touch /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/outputs/state/${IAC_ACTION_NAME}-${version}/success"
}

check_success_flag(){
    if [ -e ${IAC_DEPLOYMENT_STATE_DIR}/state/success ]
    then
        echo "Success flag present for ${IAC_DEPLOYMENT_NAME}, cannot execute."
        exit 0
    else
        echo "No success flag found for Deployment: ${IAC_DEPLOYMENT_NAME}"
    fi

    if [ ${IAC_DEPLOYMENT_NAME} == "rt-upgrade" ]
    then
        build_version=$(get_config_value inputs BUILD_VERSION ${IAC_LANDSCAPE_DIR}/deployments/${IAC_DEPLOYMENT_NAME}/inputs/config.yml)
        patch_version=$(get_config_value inputs PATCH_VERSION ${IAC_LANDSCAPE_DIR}/deployments/${IAC_DEPLOYMENT_NAME}/inputs/config.yml)
        version=${build_version}"-"${patch_version}
        if [ -e ${IAC_DEPLOYMENT_STATE_DIR}/state/${IAC_ACTION_NAME}-${version}/success ]
        then
            echo "Success flag present for ${IAC_DEPLOYMENT_NAME} --> ${IAC_ACTION_NAME} ${version}, cannot execute."
            echo "Skipping the stage ..."
            exit 0
        else
            echo "Success flag not present for ${IAC_DEPLOYMENT_NAME} --> ${IAC_ACTION_NAME} ${version}, continue the script."
        fi
    fi

    if [ -e ${IAC_DEPLOYMENT_STATE_DIR}/state/${IAC_ACTION_NAME}/success ]
    then
        echo "Success flag present for ${IAC_DEPLOYMENT_NAME} --> ${IAC_ACTION_NAME}, cannot execute."
        echo "Skipping the stage ..."
        exit 0
    fi
}

check_state_dir(){
    if [ -d ${IAC_DEPLOYMENT_STATE_DIR}/state ]
    then
        copy_files_to_ansible_node ${IAC_DEPLOYMENT_STATE_DIR}/state,/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/state
    fi
}

setup_python_env(){
    echo "Creating new virtual env : /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/venv"
    run_command_on_ansible_node "set -o pipefail && sudo python3 -m pip install virtualenv && python3 -m venv /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/venv"
    python_path=/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/venv/bin/python3
    mkdir -p ${IAC_DEPLOYMENT_STATE_DIR}/state
    echo $python_path > ${LANDSCAPE_ROOT}/state/${IAC_DEPLOYMENT_NAME}/state/pyvenv
    run_command_on_ansible_node "set -o pipefail && \
        ${python_path} -m pip install -U pip && \
        ${python_path} -m pip install /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/utils/apimrt_utils/dist/apimrt-1.0.0-py3-none-any.whl[\"apim-$(get_landscape_type)\"]"
    echo "Created new python virtual env ${python_path}"
}

push_secrets(){
    run_command_on_ansible_node "set -o pipefail && sudo ${python_path} /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/utils/utils/get_secrets.py -o /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/secrets.json"

    # run_command_on_ansible_node "set -o pipefail && python3 /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/utils/utils/get_secrets.py -o /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/secrets.json"

    run_command_on_ansible_node "sudo chmod 777 /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/secrets.json"
}

get_secret_value(){
    secret_data=$(run_command_on_ansible_node "cat /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/secrets.json")
    check_exit_status $? "Unable to fetch secret file"
    for data in ${1//,/ }
    do
        secret[$data]=$(echo ${secret_data} | jq .${data})
        check_exit_status $? "Fetch secrets failed for ${data}"
    done
}

create_directories_on_ansible_node(){
    for data in $*
    do
        run_command_on_ansible_node "mkdir -p ${data}"
    done
}

get_property(){
    if [ $# -eq 2 ];then
        for data in ${2//,/ }
        do
            prop[$data]=$(iac get-config -d $1 -p config.${data})
            check_exit_status $? "Fetching IAC get config config.${data}"
        done
    else
        check_exit_status 1 "Fetching IAC get config : Number of args passed is not proper : $#"
    fi
}


get_ansible_ip(){
    case $(get_landscape_type) in
    aws|alibaba)
    flag="ansible_lb_dns"
    ;;
    azure|gcp)
    flag="ansible_public_ip"
    ;;
    *)
    exit 1;;
    esac
    res=$(jq -r .${flag} ${IAC_LANDSCAPE_DIR}/state/apim-rt/deploy-vms-lb/state/state.json)
    check_exit_status $? "Fetching Data:${flag} from ${IAC_LANDSCAPE_DIR}/state/apim-rt/deploy-vms-lb/state/state.json"
    echo $res
}

get_landscape_type(){
    res=$(iac get-config -i landscape -p landscape.type)
    check_exit_status $? "Fetching landscape.type"
    if [ "$res" == "ali" ]
    then
        echo "alibaba"
    else
        echo $res
    fi
}

get_landscape_environment(){
    res=$(iac get-config -i landscape -p landscape.environment)
    case $res in
    live|prod)
    echo "prod"
    ;;
    dev)
    echo "dev"
    ;;
    *)
    echo "prod"
    ;;
    esac
}


get_ms_password(){
    res=$(iac get-config -d landscape-config -p credentials.mspassword)
    check_exit_status $? "Fetching credentials.mspassword"
    echo $res
}

get_state_data(){
    #get_state_data arg1=key_to_fetch(comma seperated aws,azure,gcp) arg2=state_file_name_where_key_is_present(path ref from landscape root directory to be passed)
    case $(get_landscape_type) in
    aws)
    flag=1
    ;;
    azure)
    flag=2
    ;;
    gcp)
    flag=3
    ;;
    alibaba)
    flag=4
    ;;
    *)
    exit 1;;
    esac

    key=$(echo $1 | cut -d "," -f $flag)
    res=$(jq -r .$key ${IAC_LANDSCAPE_DIR}/$2)
    check_exit_status $? "Fetching state data: $key from ${IAC_LANDSCAPE_DIR}/$"
    echo $res
}

check_exit_status(){
    #arg1=exit code arg2=exit reason
    if [ $1 != 0 ]
    then
        data=$2
        for key in "${!secret[@]}"
        do
            if echo "$key" | grep -q "password"; then
                value="${secret[$key]}"
                echo "Masking Key: $key"
                data=$(echo $data | sed -e s/$value/\-\*\*\*\*\*\*\*/g)
            fi
        done
        echo "********************************************************************"
        echo "The command has failed in executing : $data"
        echo "The command has failed with return code : $1"
        echo "********************************************************************"
        check_fail_command_push
        exit 1
    fi
}

check_fail_command_push(){
    echo "Checking and Pushing state data after the command has failed"
    command="ls /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/outputs/*"
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /tmp/ssh-private-key  concourseci@$(get_ansible_ip) -p ${ssh_port} "${command}"
    if [ $? -eq 0 ];then
        push_to_state retry
    fi
}

copy_files_to_ansible_node(){
    for data in $*
    do
        source=$(echo $data | cut -d "," -f 1)
        destination=$(echo $data | cut -d "," -f 2)
        echo "Copying files to ansible node : ${source} : ${destination}"
        if [ -n "$(ls ${source})" ]
        then
            scp -P ${ssh_port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r -i /tmp/ssh-private-key  $source concourseci@$(get_ansible_ip):$destination
        else
            if [ ${IAC_ACTION_NAME} == "inventory_generation" ] || [ ${IAC_ACTION_NAME} == "silent-config" ] || [ ${IAC_ACTION_NAME} == "pre-validation" ] || [ ${IAC_ACTION_NAME} == "post-validation" ] || [ ${IAC_ACTION_NAME} == "validation" ] || [ ${IAC_ACTION_NAME} == "post-action" ]
            then
                echo "Note: Skipping script copying for ${IAC_ACTION_NAME}"
            else
                check_exit_status 1 "Copying files: ${source} to ansible ${destination} "
            fi
        fi
        check_exit_status $? "Copying files: ${source} to ansible ${destination} "
    done
}

run_command_on_ansible_node(){
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /tmp/ssh-private-key  concourseci@$(get_ansible_ip) -p ${ssh_port} "set -o pipefail && ${1}"
    check_exit_status $? "Command execution on ansible failed : Command: $1"
}


push_to_state(){
    echo "Pushing data to ${IAC_DEPLOYMENT_STATE_DIR}"
    git_repo=$(echo $IAC_LANDSCAPE_GIT_REPOSITORY | sed -e s'/\.git$//'g)
    if [[ ${IAC_ACTION_NAME} == "inventory_generation" || ${IAC_ACTION_NAME} == "silent-config" ]]
    then
        path=${IAC_DEPLOYMENT_STATE_DIR}
        output_location=${git_repo}/tree/state/${IAC_DEPLOYMENT_NAME}
    else
        path=${IAC_DEPLOYMENT_STATE_DIR}/run_${date}
        output_location=${git_repo}/tree/state/${IAC_DEPLOYMENT_NAME}/run_${date}
    fi
    mkdir -p ${path}

    echo "Outputs Location ----------> ${output_location}"

    scp -P ${ssh_port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r -i /tmp/ssh-private-key concourseci@$(get_ansible_ip):/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/outputs/* ${path}
    exit_flag=$?
    #checking state folder inside output to be pushed
    command=`ls ${path}/state/* 2>/dev/null`
    if [ ${command} ]
    then
        echo "State folder data found, Pushing to state branch"
        rsync -av ${path}/state/ ${IAC_DEPLOYMENT_STATE_DIR}/state
        exit_flag=$?
    else
        echo "State folder not found"
    fi

    if [ "${1}" == "retry" ]
    then
        if [ $exit_flag -eq 0 ]; then
            echo "Retry command to push data to state Successful."
        else
            echo "Retry command also failed during Pushing data to state: ${path} "
        fi
    else
        check_exit_status $exit_flag "Pushing data to state: ${path}"
    fi
}

install_packages(){
    run_command_on_ansible_node "cd /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/utils/utils && sudo sh install_packages.sh maven"
}


clean_up(){
    run_command_on_ansible_node "rm -rf /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}"
}


copy_inputs_to_ansible_node(){
    copy_files_to_ansible_node ${IAC_DEPLOYMENT_INSTANCE_DIR}/inputs/*,/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs
}

copy_inventory_to_ansible_node(){
    copy_files_to_ansible_node ${IAC_LANDSCAPE_DIR}/state/inventory-generation/inventory,/home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs
    #change to python venv
    if [ ${IAC_DEPLOYMENT_NAME} == "inventory-generation" ]
    then
      echo "Skipping fetch inventory as the inventory is not created yet"
    else
      run_command_on_ansible_node "cd /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/utils/utils && sudo python3 fetch_inventory.py -p /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs -i /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/inventory"
      set_component_inventory
    fi

}

set_component_inventory(){
    for comp in "${apigee_components[@]}"
    do
        output=$(run_command_on_ansible_node "cat /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/${comp}_inventory")
        for data in $(run_command_on_ansible_node "cat /home/concourseci/scripts/${IAC_DEPLOYMENT_NAME}/${uuid}/inputs/${comp}_inventory")
        do
            eval "${comp}_inventory+=(\"$data\")"
        done
    done

}

get_config_value() {
    section=$1
    key=$2
    config_file=$3

    # Search for the section and key in the config file using grep and awk
    awk -F '=' -v section="$section" -v key="$key" 'BEGIN{IGNORECASE=1; section_found=0;}
    {
        # Check if section is found
        if ($0 ~ /^\['"$section"'\]/ || $0 ~ /^\['"$section"' /) {
            section_found=1;
        }
        # If section is found, check for the key
        else if (section_found && $1 == key) {
            gsub(/^[ \t]+|[ \t]+$/, "", $2);  # Remove leading/trailing spaces
            print $2;  # Print the value
            exit;  # Exit the script
        }
    }' "$config_file"
}

notify_teams(){
  echo "Triggering Notification ...."
  summary_message=$CONCOURSE_PIPELINE_NAME"-"$CONCOURSE_NOTIFY_NAME" failed"
  title="LS_REPO: "$IAC_LANDSCAPE_GIT_REPOSITORY
  URL=${ATC_EXTERNAL_URL}"/teams/"${CONCOURSE_TEAM_NAME}"/pipelines/"${CONCOURSE_PIPELINE_NAME}
  run_command_on_ansible_node "apimrt notify teams  --weburl ${CONCOURSE_NOTIFICATION_WEBHOOK} --title \"${title}\" --summary \"${summary_message}\" --sectitle \"${summary_message}\"  --concourse_url $URL"
}