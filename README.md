# Synthopedia
Software tool - Igem IITM 2023:

We have developed a user-friendly website featuring a publicly accessible web tool that serves as the interface for our dry-lab model and optimizer. Upon accessing the website, users are presented with a choice between two distinct tools: the RBS Rate Prediction Tool and the RBS Optimization Tool.

The RBS Rate Prediction Tool provides the relative expression level in terms of the RBS rate, represented on a logarithmic scale.

On the other hand, the RBS Optimization Tool  furnishes the optimized RBS sequence along with its corresponding predicted (logarithmically scaled) RBS rate.

## Steps to run
1. Clone the repo onto your machine `git clone https://github.com/catdisk04/Synthopedia.git -b master`
2. Run the following to install all the dependencies `pip install -r requirements.txt`
3. You need to create the model file locally as the interdepencdencies are package version specific. Move to the model_file folder and run the `igem_2023_final_model.py` file. Now replace the old `iGEM IITM 2023 - Final Model.joblib` file with the file you just created
4.  Move to the Synthopedia folder and run  `python manage.py runserver`. Now you are hosting the webpage on your localhost!
	6.  Go to the localhost url output by the code above command. On the home page, there are links to the predictor and optimizer. Fill the necessary fields and click "Submit" to get the desired output.
