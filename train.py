import autograd as ag
import copy
import numpy as np
import logging
import pickle

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.utils import check_random_state


from recnn.recnn import log_loss
from recnn.recnn import square_error
from recnn.recnn import adam
from recnn.recnn import grnn_init_simple
from recnn.recnn import grnn_predict_simple
from recnn.recnn import grnn_init_gated
from recnn.recnn import grnn_predict_gated
from recnn.preprocessing import apply_tf_transform
from recnn.preprocessing import create_tf_transform

logging.basicConfig(level = logging.INFO,
                    format = "[%(asctime)s %(levelname)s] %(message)s")


def train(filename_train,
          filename_model,
          regression = False,
          simple = False,
          n_features = 25,
          n_hidden = 40,
          n_epochs = 5,
          batch_size = 64,
          step_size = 0.0005,
          decay = 0.9,
          random_state = 42,
          verbose = False,
          statlimit = -1):
    # Initialization
    gated = not simple
    if verbose:
        logging.info("Calling with...")
        logging.info("\tfilename_train = %s" % filename_train)
        logging.info("\tfilename_model = %s" % filename_model)
        logging.info("\tgated = %s" % gated)
        logging.info("\tn_features = %d" % n_features)
        logging.info("\tn_hidden = %d" % n_hidden)
        logging.info("\tn_epochs = %d" % n_epochs)
        logging.info("\tbatch_size = %d" % batch_size)
        logging.info("\tstep_size = %f" % step_size)
        logging.info("\tdecay = %f" % decay)
        logging.info("\trandom_state = %d" % random_state)
    rng = check_random_state(random_state)

    # Make data
    if verbose:
        logging.info("Loading data...")
    if filename_train[-1]=="e":
        fd = open(filename_train, "rb")
        X, y = pickle.load(fd)
        fd.close()
    else:
        X, y = np.load(filename_train, allow_pickle=True)
    X = np.array(X).astype(dict)
    y = np.array(y).astype(float)
    flush = np.random.permutation(len(X))
    X,y = X[flush][:statlimit],y[flush][:statlimit]
    i=0
    
    ### delete single particles ###
    while i < len(X):
        if len(X[i]["content"])==1:
            X=np.delete(X,i)
            y=np.delete(y,i)
        else :
            i+=1      

    X = list(X)
    if verbose:
        logging.info("\tfilename = %s" % filename_train)
        logging.info("\tX size = %d" % len(X))
        logging.info("\ty size = %d" % len(y))

    # Preprocessing
    if verbose:
        logging.info("Preprocessing...")
    tf = create_tf_transform(X)

    X = apply_tf_transform(X,tf)

    # Split into train+validation
    logging.info("Splitting into train and validation...")

    X_train, X_valid, y_train, y_valid = train_test_split(X, y,
                                                          test_size = 0.1,
                                                          random_state = rng)
    del X
    del y
    # Training
    if verbose:
        logging.info("Training...")

    if gated:
        predict = grnn_predict_gated
        init = grnn_init_gated
    else:
        predict = grnn_predict_simple
        init = grnn_init_simple

    trained_params = init(n_features, n_hidden, random_state = rng)
    n_batches = int(np.ceil(len(X_train) / batch_size))
    best_score = [np.inf]  # yuck, but works
    best_params = [trained_params]
    n_iteration = np.zeros(1)

    def loss(X, y, params):
        y_pred = predict(params, X, regression = regression)
        l = square_error(y, y_pred).mean()#log_loss(y, y_pred).mean()
        return l

    def objective(params, iteration):
        rng = check_random_state(iteration % n_batches)
        start = rng.randint(len(X_train) - batch_size)
        idx = slice(start, start+batch_size)
        return loss(X_train[idx], y_train[idx], params)

    def callback(params, iteration, gradient,regression=regression):
        if iteration % 200 == 0:
            the_loss = loss(X_valid, y_valid, params)
            if the_loss < best_score[0]:
                best_score[0] = the_loss
                best_params[0] = copy.deepcopy(params)
                fd = open(filename_model, "wb")
                pickle.dump(best_params[0], fd)
		n_iteration[0]+=1
                fd.close()

            if verbose:
                if regression :
                    logging.info(
                        "%5d\t~loss(train) = %.4f\tloss(valid) = %.4f"
                        "\tbest_loss(valid) = %.4f" % (
                            iteration,
                            loss(X_train[:5000], y_train[:5000], params),
                            loss(X_valid, y_valid, params),
                            best_score[0]))
                else:
                    roc_auc = roc_auc_score(y_valid, predict(params, X_valid,regression = regression))
                    logging.info(
                        "%5d\t~loss(train) = %.4f\tloss(valid) = %.4f"
                        "\troc_auc(valid) = %.4f\tbest_loss(valid) = %.4f" % (
                            iteration,
                            loss(X_train[:5000], y_train[:5000], params),
                            loss(X_valid, y_valid, params),
                            roc_auc,
                            best_score[0]))


    for i in range(n_epochs):
        logging.info("epoch = %d" % i)
        logging.info("step_size = %.4f" % step_size)
        if regression:
            logging.info("zerovalue = %.4f" % zerovalue)

        trained_params = adam(ag.grad(objective),
                              trained_params,
                              step_size = step_size,
                              num_iters = 1 * n_batches,
                              callback = callback)
        step_size = step_size * decay


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'lol')
    parser.add_argument("filename_train", help = "File to use as training data.",type = str)
    parser.add_argument("filename_model", help = "File to use as model storage, will be created if it does not exist.", type = str)
    parser.add_argument("--regression", help = "Add this for regression use.", action = "store_true")
    parser.add_argument("--n_features", help = "Depends on your use-case, it's the number of features the sample contains. With our data formating, it's 14.", type = int, default = 14)
    parser.add_argument("--n_hidden", help = "Number of neurons in a layer of the final network.", type = int, default = 40)
    parser.add_argument("--n_epochs", help = "Number of epochs of training.", type = int, default = 5)
    parser.add_argument("--batch_size", help = "Size of your batch for gradient descent computing.", type = int, default = 64)
    parser.add_argument("--step_size", help = "Size of you gradient descent step.", type = float, default = 0.1)
    parser.add_argument("--decay", help = "Decay of your step size. Each epoch will do step_size : =  decay * step_size.", type = float, default = 0.9)
    parser.add_argument("--random_state", help = "Set a random state. Default is 42.", type = int, default = 42)
    parser.add_argument("--statlimit", help = "Limit sample size (usefull for ram usage).", type = int, default = -1)
    parser.add_argument("--verbose", help = "Verbose.", action = "store_true")
    parser.add_argument("--simple", help = "Add this to use a simple network instead of a gated one.", action = "store_true")
    args = parser.parse_args()

    filename_model = args.filename_model.replace('iteration.','iteration{}.')
    
    train(filename_train = args.filename_train,
          filename_model = filename_model,
          regression = args.regression,
          simple = args.simple,
          n_features = args.n_features,
          n_hidden = args.n_hidden,
          n_epochs = args.n_epochs,
          batch_size = args.batch_size,
          step_size = args.step_size,
          decay = args.decay,
          random_state = args.random_state,
          verbose = args.verbose,
          statlimit = args.statlimit)
