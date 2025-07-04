Run this to collect the latest FlixBus currency biases:

```
python main.py > "./latest-prices.txt"
```

FlixBus does service in lots of different countries. They change their prices depending on which of the company's regional websites you're using.

Of course, not all prices are made equally. To my knowledge, only transactions paid with USD, GBP, or EUR incur an additional service fee. Also, currencies shift up or down with each other.

I've observed that using FlixBus with USD is the most expensive option (don't forget the $3.99 service fee) whereas the best currency usually changes over the years. For example, on 2024-11-18, Canadian dollars used to cost 93% as much as US dollars. However, as of 2025-02-15, CAD-to-USD was priced at 98% and other currencies reach as low as 92%.

Data is collected from an average of prices given for trips between Los Ángeles and Las Vegas set to take place 7 days from the date of last update.
