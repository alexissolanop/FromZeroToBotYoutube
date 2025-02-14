from TradingDTOs import Amount, PnlOption
import time

# Trading Configuration
sol_buy_amount = Amount.sol_ui(.0001)
slippage = Amount.percent_ui(13)
priority_fee = Amount.sol_ui(.0001)
PRIORITY_FEE_INCREMENT_SOL = 0.0001
MAX_FEE_RETRIES = 5
PRIORITY_FEE_MAX_SOL = 0.005
profit_limit = PnlOption(trigger_at_percent = Amount.percent_ui(600), allocation_percent = Amount.percent_ui(100))
stop_loss = PnlOption(trigger_at_percent = Amount.percent_ui(-15), allocation_percent = Amount.percent_ui(100))




# Refresh intervals
PRICE_REFRESH_INTERVAL = 300  # 5 minutes
FEAR_GREED_REFRESH_INTERVAL = 1800  # 30 minutes

# Last update timestamps
last_price_update = time.time()
last_fear_greed_update = 0

# Previous values for detecting changes
previous_sol_price = None
previous_fear_greed = None
previous_token_accounts_dict = None
colorized_index = None
classification = None
sol_price = None
