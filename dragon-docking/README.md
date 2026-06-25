# Dragon SpaceX Automated Docking

SpaceX has provided a [simulator](https://iss-sim.spacex.com/) interface for Dragon SpaceX docking process. It is very similar to the actual interface in the Dragon Vehicle. This repository provides a framework to build automated docking solutions for this simulator using Python and Selenium. It also provides a basic docking-automator-bot, which interacts with the interface to complete the docking process completely on its own. You can play around with the code, and build/train your own bot to do the automated docking.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for testing and development purposes.

### Prerequisites

You will need **Python3** and **pip** installed on your machine to run this project.

### Step by step guide

Let's create a directory and get python virtualenv setup.

```
mkdir spacex_docking
```

```
cd spacex_docking
```

```
virtualenv env_spacex
```

```
source env_spacex/bin/activate
```


Next, we will clone this repository on your machine.

```
git clone https://srp201201051@bitbucket.org/srp201201051/dragon-docking.git
```

After that, we will install the required python packages.

```
cd dragon-docking
```

```
pip install -r requirements.txt
```


Then, we will fire up a Firefox session, which will be used by our scripts to interact with the website. This might take a while, as the initial loading of the website is quite slow sometimes. Once, the webpage is loaded, you can click on the "Begin" button, and play around with the simulator. It should create a **session_data.json** file containing the Firefox session details.

```
python3 create_firefox_session.py
```


Now, we would like to keep this session open, so that we do not have to wait for initial website loading every time we want to run a script. So, open up a new terminal tab/window. We will run our bot in this window to complete automated docking. Run below commands in the new terminal tab/window.

```
cd spacex_docking
```

```
source env_spacex/bin/activate
```

```
cd dragon-docking
```

#### To use the traditional bot
```
python3 traditional/automated_docking.py
```

#### To use the supervised learning bot
```
python3 supervised_learning/training_data_generator_discrete.py 
```

```
python3 supervised_learning/decision_tree_model_discrete.py 
```

```
python3 supervised_learning/automated_docking.py
```


Yay, we are done with running our bots to dock the Dragon Vehicle. You can type EXIT and press enter any time to exit the Firefox session in the firt terminal window.
