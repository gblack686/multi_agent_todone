# ATL

## Git Worktree validation-workflow
[✅ 3ecdebb33, 17b93f48] Add a row to apps/sentiment_classification/data/tweets_v1.csv
[✅ 3ecdebb33, 267fa7a9] build a simple classification model to classify sentiment of a tweet. Use the apps/sentiment_classification/data/tweets_v1.csv dataset.
[✅ 3ecdebb33, 333fe96b] execute main.py and report the results to main_output.txt next to the main file
[✅ 981fc7982, 4f87690d] create a new tweets_v2 dataset with 200 rows of a new dataset
[✅ 981fc7982, 05e5d6f6] add docs so we understand how to use the predict.py method. create these docs in app_docs/tweet_sentiment.md. showcase how we can use it against our tweets_v1 and v2 csv datasets. {opus}
[✅ 981fc7982, b3ea5f5b] separate predict.py. Create a dedicated jupyter notebook for training the model. Then pass in the model into predict.py as well as a tweet. {sonnet,adw_plan_implement_update_task}. validate your work. 
[✅ f395e05c6, d2a6998f] Execute the predict.py method against the tweets_v1.csv dataset and report the results to predict_main_output.txt next to the main file

## Git Worktree classify-primary-topic
[✅ 85e33938e, bbc2a077] Build a new primary topic classifier model. Use the tweets_v1.csv dataset. Use the same approach as the sentiment classifier except build the a new model (notebook) and predictor/classifier (python file) to classify the primary topic of a tweet, given existing topics (training) and a new tweet (prediction). {sonnet,adw_plan_implement_update_task}

## Git Worktree edgecase-tweets
[✅ df5241b6d, fc290303] Add 25 edge case tweets (emojis, special characters, mixed languages) to data/tweets_edge_cases.csv for testing
[✅ 8b74b8119, edcc8b72] Add 30 more edge case tweets into data/tweets_edge_cases.csv for testing

## Git Worktree create-topic-filter
[✅ f640f0fc2, 891ff06d] Generate filtered dataset at data/tweets_tech_topics.csv containing only technology and entertainment topics from tweets_v1.csv
[✅ 815dad6da, 280149f7] Add 30 new tweets about sports and recreation to expand topic diversity in tweets_v1.csv
[✅ dc9d481df, ead539f1] Add 15 new tweets about meme and meme culture to expand topic diversity in tweets_v1.csv