
from __future__ import print_function
import time
import datetime
import logging
import re
from homeassistant.util import dt

REQUIREMENTS = ['ynab-client==0.1.8']
DOMAIN = 'ynab_gateway'
VERSION = '0.1.0'

CONF_BUDGET_ID = 'budget_id'
CONF_API_KEY = 'api_key'
CONF_DEFAULT_ACCOUNT = 'default_account'
CONF_SHOW_ACCOUNTS = 'show_accounts'
CONF_DEFAULT_ACCOUNT_NAME = 'default_account_name'

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    import ynab_client
    from ynab_client.rest import ApiException
    from ynab_client.models.save_transaction  import SaveTransaction
    from ynab_client.models.save_transaction_wrapper import SaveTransactionWrapper

    conf = config[DOMAIN]
    # Configure API key authorization: bearer
    configuration = ynab_client.Configuration()
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = conf.get(CONF_API_KEY)
    categories = []
    api_instance = ynab_client.TransactionsApi() # ynab_client.ApiClient(configuration)
    _LOGGER.info(conf)
    _LOGGER.info(conf.get(CONF_API_KEY))
    _LOGGER.info(conf.get(CONF_BUDGET_ID))
    _LOGGER.info(conf.get(CONF_DEFAULT_ACCOUNT))
    _LOGGER.info(conf.get(CONF_DEFAULT_ACCOUNT_NAME))

    if conf.get(CONF_SHOW_ACCOUNTS):
        accounts = ynab_client.AccountsApi()
        _LOGGER.info(accounts.get_accounts(conf.get(CONF_BUDGET_ID)))
    try:
        cat_api = ynab_client.CategoriesApi()
        cat_groups = cat_api.get_categories(conf.get(CONF_BUDGET_ID)).data


        # _LOGGER.info(cat_groups)

        # Flatten category structure returned and print to log
        cat_string = "categories:"
        for group in cat_groups.category_groups:
            for cat in group.categories:
                slug = replaceMultiple(replaceMultiple(cat.name, ['(', ')', '/','$','&'] , ""), [' ', ','],"_")
                c = {}
                c['id'] = cat.id
                c['name'] = cat.name
                c['slug'] = slug
                cat_string = cat_string + "\n\t- name: \"" + cat.name + "\"\n\t  id: \"" + cat.id + "\"\n\t  slug: \"" + slug + "\""
                categories.append(c)

        _LOGGER.info(cat_string)

        _LOGGER.info(categories)
    except ApiException as e:
        _LOGGER.info("Exception when calling TransactionsApi->create_transaction: %s\n" % e)
        return e
    # Listener to handle fired events
    async def handle_webhook(hass, webhook_id, request):

        body = await request.json()
        _LOGGER.info(body)

        regex = r"\$(\d*)\.(\d*).*at\s*([\w\s]*[^\s])\s*on\s*([\w\s]*)"

        matches = re.findall(regex, body['message'], re.MULTILINE)
        if True: #len(matches) == 1:
            _LOGGER.info(matches)
            match = matches[0]
            
            dollars = match[0]
            cents = match[1]

            _LOGGER.info(dollars)
            _LOGGER.info(cents)
            payee = match[2]
            _LOGGER.info(payee)

            category = match[3]
            _LOGGER.info(category)
    

            transaction = SaveTransaction(
                date= dt.as_local(dt.now()), 
                amount=(int(dollars)*100+int(cents))*10,
                cleared='cleared',
                approved=False,
                account_id=conf.get(CONF_DEFAULT_ACCOUNT)
            )

            # best_payee 


            
            # log_data = {
            #     'name': "FdS",    
            #     'message': transaction
            # }
            # resolve payee using list of known payees and return payee_name to use in ynab
            # transaction["payee_name"] = resulting_payee_name

            payload = SaveTransactionWrapper(transaction)
            # transactionwrapper.transaction = transaction
            # resolve payee and assign category accordingly

            # hass.services.call('logbook', 'log', log_data)

            try:
                api_response = api_instance.create_transaction(conf.get(CONF_BUDGET_ID), payload)
                _LOGGER.info(api_response)
                return  api_response.to_str()
            except ApiException as e:
                _LOGGER.info("Exception when calling TransactionsApi->create_transaction: %s\n" % e)
                return e
        else:
            _LOGGER.info("Unexpected number of matches" + matches)

    
    # Listen for when my_cool_event is fired
    hass.components.webhook.async_register(  DOMAIN, 'Bank transactions', 'ynab', handle_webhook)
        
    _LOGGER.info(
    "Bank transactions webhook available on:" + hass.components.webhook.async_generate_url('ynab')
    )

    return True


def get_best_payee_cat(categories, payee):
    known_payees = [
        {name: "Aldi", sub: "Aldi"},
        {name: "Big W", sub: "Big W"}

    ]
    the_payee = None
    for p in known_payees:
        if payee.contains(p.sub):
            _LOGGER.info("Best payee is " + p.name)
            the_payee = p
    return the_payee.name, the_payee.category

# def get_cat_by_payee


'''
Replace a set of multiple sub strings with a new string in main string.
'''
def replaceMultiple(mainString, toBeReplaces, newString):
    # Iterate over the strings to be replaced
    for elem in toBeReplaces :
        # Check if string is in the main string
        if elem in mainString :
            # Replace the string
            mainString = mainString.replace(elem, newString)
    
    return  mainString