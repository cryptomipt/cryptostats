import os
import sys
import json

import statstools.stats as stats

if __name__ == '__main__':
    if len(sys.argv) == 1:
        keys_path = "./keys.json"
    else:
        keys_path = sys.argv[1]

    if not os.path.isfile(keys_path):
        print("Can't find `keys.json` file. See `keys_template.json`.")
        exit()

    with open(keys_path, 'r') as fin:
        keys = json.load(fin)

    for key in keys:
        exchange = stats.login(key)
        # TODO: add colors to this line
        print('Exchange: {}'.format(key['Description']))

        try:
            change_info = stats.get_portfolio_info(exchange)
            stats.print_portfolio_info(change_info)
        except Exception as e:
            print('Failed to get data for {}. Reason: {}'.format(
                key['Description'], e))
            continue
        print()
