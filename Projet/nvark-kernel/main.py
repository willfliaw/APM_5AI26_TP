import numpy as np
import pandas as pd
import time

from load_dataset import load_dataset, print_info, preprocessing

# NVARk
from model.NVARk import NVARk
from model.emb_pars import SSR_parameters

# # different tasks
# from sklearn.svm import SVC

# internal imports
import utils
import tasks

import warnings

warnings.filterwarnings("ignore")


datasets_list = [
    # "EmoDB",
    # "RAVDESS",
    "HAR",
]

"""global variables"""
# set to 'zero_padding' for matching the longest series in the dataset
# set to 'interpolate'
prepr_option = "zero_padding"  # 'none' / 'zero_padding' / 'interpolate'
experiment = "SVM_NVARk"  # SVM_NVARk, SVM_NVARk* , time_NVARk
random_iterations = 10
svm_C_list = np.logspace(-3, 3, 7)
# 'svd' or 'cholesky'  ('cholesky' is used in the paper, is faster but can be unstable for matrices with high collinearity)
solver = "svd"


def main():
    """################# Data Loading ##########################################"""
    for dataset_name in datasets_list:
        print("Reading dataset: ", dataset_name)

        TRAIN_x_raw, TRAIN_y_raw, TEST_x_raw, TEST_y_raw = load_dataset(dataset_name)

        print("Dataset reading is completed")

        info = print_info(dataset_name, TRAIN_x_raw, TEST_x_raw, y=TRAIN_y_raw)
        T_min_init = min(
            info[dataset_name + " train"]["T_min"],
            info[dataset_name + " test"]["T_min"],
        )
        if prepr_option == "zero_padding":
            T_max = max(
                info[dataset_name + " train"]["T_max"],
                info[dataset_name + " test"]["T_max"],
            )
        elif prepr_option == "interpolate":
            T_max = 25

        """################# Preprocessing #################################"""
        TRAIN_x, TRAIN_y, TEST_x, TEST_y = preprocessing(
            dataset_name,
            prepr_option,
            TRAIN_x_raw,
            TRAIN_y_raw,
            TEST_x_raw,
            TEST_y_raw,
            T_new=T_max,
            info=info,
        )
        info = print_info(dataset_name, TRAIN_x, TEST_x, y=TRAIN_y)
        print("\n")

        # convert datasets of panda series to a list of 2D numpy arrays (shape = [[N], T, D])
        TRAIN_x_l = utils.pdSeriesDataFrame_to_listOfnpArray(TRAIN_x)
        TEST_x_l = utils.pdSeriesDataFrame_to_listOfnpArray(TEST_x)

        """################# NVAR model ##########################################"""
        # get embedding parameters
        T_min = min(
            info[dataset_name + " train"]["T_min"],
            info[dataset_name + " test"]["T_min"],
        )
        filter_scale = 1 / (20 * T_min)
        k_sqrt, s_sqrt, _, _, _ = SSR_parameters(
            TRAIN_x_l, T_min, filter_data=True, filter_scale=filter_scale, plot=False
        )
        k = k_sqrt
        s = s_sqrt
        if k * s >= T_min_init:
            while k * s >= T_min_init:
                k = k - 1
                s = s - 1
        params = {"k": k, "n": 2, "s": s, "n_dim": 75, "lamb": None, "gamma_mult": 1}

        """ individual steps to output K tr-tr """
        # model        = NVARk(**params, repr_mode='ridge', random_state=1, verbose_lvl=2, solver=solver)
        # _            = model.sample_indices(TRAIN_x_l)
        # R_nvar       = model.compute_embedding(TRAIN_x_l) # list of 2D np arrays
        # theta_repr   = model.linear_readout(R_nvar) # 2D np arrays
        # K            = model.rbf_function(theta_repr) # 2D np arrays

        """ RUNNING TIME: output matrices in one call and compute running time"""
        if experiment == "time_NVARk":
            st_time = time.perf_counter()
            model = NVARk(
                **params,
                repr_mode="ridge",
                random_state=1,
                verbose_lvl=2,
                solver=solver,
            )
            K_trtr = model.compute_Ktrtr(TRAIN_x_l)
            K_tetr = model.compute_Ktetr(TEST_x_l, TRAIN_x_l)
            end_time = time.perf_counter()
            print("time = ", round(end_time - st_time, 3), "s")

        """ NVARk GENERAL SETTING """
        if experiment == "SVM_NVARk":
            # mean over more iters
            best_test_acc = 0
            best_labels = []

            test_acc_all = []
            train_acc_all = []
            prec_all = []
            rec_all = []
            f1_all = []

            for i in range(1, random_iterations + 1):
                print(f"iteration {i}")
                if i == 1:
                    verbose_lvl = 2
                else:
                    verbose_lvl = 0
                model = NVARk(
                    **params,
                    repr_mode="ridge",
                    random_state=i,
                    verbose_lvl=verbose_lvl,
                    readout_type="SVM",
                    solver=solver,
                )
                K_trtr = model.compute_Ktrtr(TRAIN_x_l)
                K_tetr = model.compute_Ktetr(TEST_x_l, TRAIN_x_l)
                (
                    labels_test,
                    acc_test,
                    acc_train,
                    prec_train,
                    rec_train,
                    f1_train,
                    best_C,
                ) = tasks.my_SVMopt_classifier(
                    K_trtr,
                    TRAIN_y,
                    K_tetr,
                    TEST_y,
                    svm_C_list,
                    i,
                    n_folds=10,
                    val_size=0.33,
                    verbose=False,
                )

                test_acc_all.append(acc_test)
                train_acc_all.append(acc_train)
                prec_all.append(prec_train)
                rec_all.append(rec_train)
                f1_all.append(f1_train)

                if acc_test > best_test_acc:
                    best_labels = labels_test
                    best_test_acc = acc_test

            # create a final array : each column is a metric and each row is an iteration
            train_results = np.array([train_acc_all, prec_all, rec_all, f1_all]).T

            np.save(f"results/{dataset_name}_testlabels.npy", np.array(best_labels))

            np.save(f"results/{dataset_name}_trainmetrics.npy", train_results)

            print(
                "mean test accuracy = ",
                round(np.mean(test_acc_all), 3),
                " +- ",
                round(np.std(test_acc_all), 3),
            )

        """ NVARk* OPTIMIZED SETTING """
        if experiment == "SVM_NVARk*":
            """optimize params via CV"""
            D = TRAIN_x_l[0].shape[1]
            if D > 1:
                if T_min < 60:
                    k_list = list(set([1, 2, 3, 4, k]))
                    s_list = list(set([1, 2, 3, 4, s]))
                elif T_min >= 60:
                    k_list = list(set([1, 2, 3, 4, 10, 20, k]))
                    s_list = list(set([1, 5, 20, s]))
            else:
                if T_min < 400:
                    k_list = list(set([1, 2, 3, 4, 5, k]))
                    s_list = list(set([1, 2, 3, 4, 5, s]))
                elif T_min >= 400:
                    k_list = list(set([1, 2, 3, 4, 5, 10, 20, k]))
                    s_list = list(set([1, 5, 10, 20, s]))
            n_dim_list = [75]

            # optimize
            model = NVARk(
                n=2,
                repr_mode="ridge",
                random_state=1,
                verbose_lvl=1,
                readout_type="SVM",
                gamma_mult=1,
                solver=solver,
            )
            model.optimize_params(
                TRAIN_x_l,
                TRAIN_y,
                k_list,
                s_list,
                n_dim_list,
                svm_C_list,
                n_folds=10,
                val_size=0.33,
                n_jobs=-1,
                random_state=1,
                split="stratified",
            )
            accuracy = []
            for i in range(1, random_iterations + 1):
                print(f"iteration {i}")
                model.random_state = i
                # evaluate
                # mean over more iters
                if i == 1:
                    model.verbose_lvl = 2
                else:
                    model.verbose_lvl = 0
                model.fit(TRAIN_x_l, TRAIN_y)
                accuracy.append(model.score(TEST_x_l, TEST_y))

            print(
                "accuracy = ",
                round(np.mean(accuracy), 3),
                " +- ",
                round(np.std(accuracy), 3),
            )

            # alternative loop in which params are optimized in each iteration with different seed
            # best embedding parameters and best SVM parameters are found for each terms sampling in NVARk
            # should lead to slightly better result
            # accuracy=[]
            # for i in range(1,random_iterations+1):
            #       print(f'iteration {i}')

            #       # optimize
            #       model = NVARk(n=2, repr_mode='ridge', random_state=i, verbose_lvl=1, readout_type='SVM', gamma_mult=1, solver=solver)
            #       st_time = time.perf_counter()
            #       model.optimize_params(TRAIN_x_l, TRAIN_y,
            #                         k_list, s_list, n_dim_list, svm_C_list,
            #                         n_folds=10, val_size=0.33, n_jobs=-1, random_state=i,
            #                         split='stratified')
            #       opt_time = time.perf_counter()-st_time
            #       print(f'optimization time = {round(opt_time,3)}')
            #       # evaluate
            #       # mean over more iters
            #       if i==1:model.verbose_lvl = 2
            #       else:   model.verbose_lvl = 0
            #       model.fit(TRAIN_x_l, TRAIN_y)
            #       accuracy.append(model.score(TEST_x_l, TEST_y))

            # print('accuracy = ', round(np.mean(accuracy),3) , ' +- ', round(np.std(accuracy),3))


if __name__ == "__main__":
    main()
