import random
import time
import enum
import constants


from osbrain import Agent, run_agent, run_nameserver


class AuctionSync(Agent):

    def on_init(self):
        self.current_market_prices = 0
        self.seller_agents = []

    def generate_market_prices(self):
        self.current_market_prices = random.randrange(1, 100)

    def send_market_prices(self):
        self.send('marketPrices', self.current_market_prices)
        self.log_info(
            f"Market prices sent! Current price: {self.current_market_prices}")

    def gather_sellers(self, agent_number):
        address_alias = f"requestSeller{agent_number}"
        self.send(address_alias, 'Will you sell?')
        if self.recv(address_alias):
            self.seller_agents.append(agent_number)
        self.log_info("Sellers gathered!")

    def reset_seller_list(self):
        self.seller_agents = []

    def auction(self):
        self.log_info(f"Started auction with {self.seller_agents}")


class Prosumer(Agent):
    def on_init(self):
        self.next_energy_consumption = 0
        self.next_energy_generation = 0
        self.predictions_at = 18
        self.calculations_at = 21
        self.store_data = True
        self.is_seller = False
        self.energy_difference = 0
        self.energy_market_price = 0
        self.wanted_energy = 0
        self.energy_buying_max_price = 0
        self.energy_buying_starting_price = 0
        self.energy_buy_price_increment = 0
        self.energy_selling_min_price = 0
        self.energy_sold = False
        self.buy_parameters = {
            constants.BASELINE: constants.buy_baseline.deficit,
            constants.ENERGY: 80,
            constants.MAX_PRICE: 90,
            constants.START_PRICE: 30,
            constants.INCREMENT: 10,
        }
        self.sell_parameters = {
            constants.BASELINE: constants.sell_baseline.surplus,
            constants.ENERGY: 80,
            constants.MIN_PRICE: 110,
            constants.MAX_LOT_SIZE: 100
        }

    def predict_energy(self):
        self.next_energy_consumption = random.randrange(1, 100)
        self.next_energy_generation = random.randrange(1, 100)
        self.log_info(
            f"Predicted Consumption: {self.next_energy_consumption}; Generation: {self.next_energy_generation}")

    def get_bids(self):
        self.energy_difference = self.next_energy_generation - self.next_energy_consumption
        self.is_seller = self.energy_difference < 0

        if self.is_seller:
            self.energy_difference *= -1
            self.wanted_energy = self.calculate_sell_energy()
            self.log_info(f"Will sell! Wanted energy: {self.wanted_energy}")
        else:
            self.wanted_energy = self.calculate_buy_energy()
            self.log_info(f"Will Buy {self.wanted_energy}")

    def calculate_buy_energy(self):
        baseline = self.buy_parameters[constants.BASELINE]
        sell_energy = 0

        if(baseline == constants.buy_baseline.deficit):
            sell_energy = self.energy_difference
        elif(baseline == constants.buy_baseline.all_energy):
            sell_energy = self.next_energy_consumption
        elif(baseline == constants.buy_baseline.infinite):
            sell_energy = 99999
        else:
            sell_energy = 0

        sell_energy *= self.buy_parameters[constants.ENERGY] / 100
        return sell_energy

    def calculate_sell_energy(self):
        baseline = self.sell_parameters[constants.BASELINE]
        sell_energy = 0

        if(baseline == constants.sell_baseline.all_energy):
            sell_energy = self.next_energy_generation
        elif(baseline == constants.sell_baseline.surplus):
            sell_energy = self.energy_difference
        else:
            sell_energy = 0

        sell_energy *= self.sell_parameters[constants.ENERGY]/100
        return sell_energy

    def get_market_prices(self, message):
        market_price = int(message)
        self.energy_market_price = int(message)

        self.energy_buying_starting_price = market_price * \
            self.buy_parameters[constants.START_PRICE] / 100
        self.energy_buy_price_increment = self.energy_market_price * \
            self.buy_parameters[constants.INCREMENT] / 100
        self.energy_buying_max_price = self.energy_market_price * \
            self.buy_parameters[constants.MAX_PRICE] / 100
        self.energy_selling_min_price = self.energy_market_price * \
            self.sell_parameters[constants.MIN_PRICE] / 100
        self.log_info(
            f"Prices gathered! Market: {self.energy_market_price}; Buy Start: {self.energy_buying_starting_price}; Buy Increment: {self.energy_buy_price_increment}; Buy Max: {self.energy_buying_max_price}; Sell Min: {self.energy_selling_min_price}")

    def answer_sell_request(self, message):
        return self.is_seller


class MultiagentSystem():

    def __init__(self):
        self.current_messages = []

        '''Agent Setup'''
        # Setting up nameserver
        self.nameserver = run_nameserver()

        # Setting up auction sync
        self.auction_sync_agent = run_agent('auction_sync', base=AuctionSync)

        # Setting up agents
        self.agent_amount = constants.NAMESERVER_AGENT_AMOUNT
        self.prosumers = []

        for i in range(self.agent_amount):
            agent_name = f"Prosumer{i}"
            self.prosumers.append(run_agent(agent_name, base=Prosumer))

        '''Communications Setup'''
        # Sell request set up
        requested_seller_addresses = []
        for i in range(self.agent_amount):
            addrAlias = f"requestSeller{i}"
            requested_seller_addresses.append(self.prosumers[i].bind(
                'REP', alias=addrAlias, handler=Prosumer.answer_sell_request))
            self.auction_sync_agent.connect(
                requested_seller_addresses[i], alias=addrAlias)

        # Market price set up
        marketPriceAddr = self.auction_sync_agent.bind(
            'PUB', alias='marketPrices')
        for new_prosumer in self.prosumers:
            new_prosumer.connect(
                marketPriceAddr, handler=Prosumer.get_market_prices)

    def run_auction_script(self):
        self.auction_sync_agent.each(5, AuctionSync.send_market_prices)
        time.sleep(1)
        for current_agent in range(self.agent_amount):
            self.prosumers[current_agent].each(5, Prosumer.predict_energy)
        time.sleep(1)
        for current_agent in range(self.agent_amount):
            self.prosumers[current_agent].each(5, Prosumer.get_bids)
        time.sleep(1)
        self.auction_sync_agent.each(5, AuctionSync.reset_seller_list)
        for i in range(self.agent_amount):
            self.auction_sync_agent.each(
                5, AuctionSync.gather_sellers, i)
        time.sleep(1)
        self.auction_sync_agent.each(5, AuctionSync.auction)

    def update_messages(self):
        self.current_messages.append()

    def shutdown(self):
        self.nameserver.shutdown()


if __name__ == "__main__":
    mas = MultiagentSystem()
    mas.run_auction_script()
