from uuid import uuid4
from htmh_l2vpn.access_handler.access_handler import AccessHandler

if __name__ == '__main__':
    access_hd = AccessHandler()
    active_services = {}

    while True:
        print('\nPlease select an option:')
        option = input(
            """
0. Set normal functions
1. Create a L2 VPN
2. Delete a L2 VPN
3. Refresh Service
4. Print Active Services
5. Exit
""")
        if option == '0':
            access_hd.set_normal_functions()

        elif option == '1':
            selected_devices = []

            while True:
                sw_input = input("\n Type 'back' to come back or the name of the sw: ")
                if sw_input.lower() == 'back':
                    break
                selected_devices.append(sw_input)

            all_tokens = list(active_services.keys())
            while True:
                service_token = str(uuid4())
                if service_token not in all_tokens:
                    break

            access_hd.create_l2vpn(devices=selected_devices, service_token=service_token)
            print("\nThe Service Token is: " + service_token)
            active_services.update({service_token: selected_devices})

        elif option == '2':
            while True:
                service_token_input = input("\n Please, type the provided Service Token (type 'back' to get back): ")
                if service_token_input == 'back':
                    break
                elif service_token_input in active_services.keys():
                    access_hd.delete_l2vpn(active_services[service_token_input], service_token_input)
                    active_services.pop(service_token_input)
                    print("Service removed successfully")
                    break

                else:
                    print("Service Token is not valid")

        elif option == '3':
            while True:
                service_token_input = input("\n Please, type the provided Service Token (type 'back' to get back): ")
                if service_token_input == 'back':
                    break
                elif service_token_input in active_services.keys():
                    access_hd.set_normal_functions()
                    access_hd.delete_l2vpn(devices=active_services[service_token_input],
                                           service_token=service_token_input)
                    access_hd.create_l2vpn(devices=active_services[service_token_input],
                                           service_token=service_token_input)

                    print("Host added")
                    break

                else:
                    print("Service Token is not valid")

        elif option == '4':
            print('')
            print(active_services)

        elif option == '5':
            print('Stopping...')
            break
