import numpy as np
import time
from sklearn.model_selection import ShuffleSplit
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from sklearn.datasets import load_breast_cancer
from sklearn.datasets import load_wine
from sklearn.datasets import load_digits
from sklearn.tree import DecisionTreeClassifier

def class_counts( data):
    """
    Helper Function

    Counts the number of label classes for an array of data.
    Because the label is in the last index of every row, this is easy
    Called from both a Leaf Node when outputing predictions and Tree when
    determining Gini / info gain of a potential split
    """
    counts = {}
    for row in data:
        label = row[-1]
        if label not in counts:
            counts[label] = 0
        counts[label] += 1
    return counts

def get_random_subsets(X, y, n_subsets, replacements=True):
    """ Return random subsets (with replacements) of the data """
    n_samples = np.shape(X)[0]

    # Concatenate x and y and do a random shuffle
    X_y = np.concatenate((X, y.reshape((1, len(y))).T), axis=1)
    np.random.shuffle(X_y)
    subsets = []

    # Uses 50% of training samples without replacements
    subsample_size = int(n_samples // 2)
    if replacements:
        subsample_size = n_samples      # 100% with replacements
    for _ in range(n_subsets):
        idx = np.random.choice(
            range(n_samples),
            size=np.shape(range(subsample_size)),
            replace=replacements)
        X = X_y[idx][:, :-1]
        y = X_y[idx][:, -1]
        subsets.append([X, y])
    return subsets

class Question:
    """
    A Question is used to partition a dataset.
    This class records the column/feature and the value that
    we are comparing with or "splitting on"
    """
    def __init__( self, feature, value ):
        self.feature = feature
        self.value = value

    def match( self, against ):
        return against[self.feature] >= self.value


class Node:
    """
    A node is either a decision node, or the last "leaf" on a branch.

    If the node is a decision node, it contains a reference to the question,
    and a reference to the recursive true and false branchs.
    A decision will not exist unless there is BOTH a true and false branch,
    and the number of samples in both of these nodes is greater than the early
    stopping criteria.

    If the node is a leaf then it holds a dictionary of the
    classes and the number of times this class appears in the training data
    reaching this leaf.
    """
    def __init__(
        self,
        is_decision = 0,
        rows = None,
        question = None,
        true_branch = None,
        false_branch = None
    ):
        if is_decision is 1:
            self.is_decision = 1
            self.question = question
            self.true_branch = true_branch
            self.false_branch = false_branch
        else:
            self.is_decision = 0;
            self.predictions = class_counts( rows )

    # This will be not be called unless the leaf is a node.
    def top_pick( self ):
        best_class = 0;
        best_number = 0
        for pred_class, pred_number in self.predictions.items():
            if pred_number > best_number:
                best_class = pred_class
                best_number = pred_number
        return best_class


class Tree():
    """
    A Tree begins with a root node, which is eiher a leaf (Not a great tree...)
    or a decision node. The decision node is split on the optimal attribute
    and value of that attribute that results in the most information gain.
    Then each branch of this initial decision node is recursively generated
    through the same process, until we reach a stopping criteria.
    """
    def __init__(self, stopping_criteria = 0, root_node = None):
        self.stopping_criteria = stopping_criteria
        self.root_node = None

    # Methods to match skilearn interface specification
    def get_params(self, deep=True):
        return {

            "stopping_criteria": self.stopping_criteria,
            "root_node": self.root_node
        }


    # Methods to match skilearn interface specification
    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self


    def partition( self, rows, question):
        """
        Partitions a dataset.
        For each row in the dataset, check if it matches the question.
        If so, add it to true_rows otherwise add it to false_rows
        """
        true_rows   = []
        false_rows  = []
        for row in rows:
            if question.match( row ):
                true_rows.append( row )
            else:
                false_rows.append( row )
        return true_rows, false_rows


    def gini( self, rows):
        """
        Calculate the Gini for a list of rows.
        """
        counts = class_counts( rows )
        impurity = 1
        samples = float( len( rows ))
        for label in counts:
            label_p = counts[label] / samples
            impurity -= label_p**2
        return impurity


    def info_gain( self, left, right, current_uncertainty):
        """
        Information Gain.
        """
        prob_left = float( len( left ) ) / ( len( left ) + len( right ) )
        prob_right = 1 - prob_left
        info_gain = current_uncertainty;
        info_gain -= prob_left * self.gini( left )
        info_gain -= prob_right * self.gini ( right )
        return info_gain


    def find_best_split( self, rows ):
        """
        Find the best question to ask by iterating over every
        feature / value and calculating the information gain
        """
        most_gain = 0  # keep track of the best information gain
        best_question = None  # keep train of the column / Value that produced best gain
        current_gini = self.gini( rows )

        # for each feature, col here equals 1 feature
        for col in range( len( rows[0] ) - 1 ):
            # unique values in the colum
            values = set( [row[col] for row in rows] )
            # for each value
            for val in values:
                q = Question( col, val )
                true_rows, false_rows = self.partition( rows, q )

                # If one branch has length less than our stopping_criteria then no split
                if len( true_rows ) < self.stopping_criteria or len( false_rows ) < self.stopping_criteria:
                    continue

                # Calculate the information gain from this split
                g = self.info_gain( true_rows, false_rows, current_gini )

                # If this gain is better than present best gain, record
                if g >= most_gain:
                    most_gain = g
                    best_question = q

        return most_gain, best_question


    def fit( self, x, y, stopping_criteria = 0 ):
        """
        Importing training data and setting stopping criteria

        Create a new 2d numpy array.
        Append the target class, for ever array of data labels giving us:
        merged_train[i] = [ x[i][0], x[i][1], x[i][2], x[i][3], y[i] ]
        This reduces the complexity because we don't have to pass on two arrays
        """
        merged_train = np.empty( [len( x ), len( x[0] ) + 1] )
        for i in range( len( x ) ):
            merged_train[i] = np.append( x[i], y[i] )

        if stopping_criteria != 0:
            self.stopping_criteria = stopping_criteria
        else:
            self.stopping_criteria = len( merged_train ) / 10

        # Start the intial building of the tree via recursive building
        self.root_node = self.build(merged_train)


    def build( self, rows ):
        """
        Builds the tree.
        Recursive AF!
        """

        # Determine the best attribute and split value that gives most info gain
        gain, question = self.find_best_split( rows )

        # This is the base case, no further info gain to be made. Stop Recursion
        if gain == 0:
            return Node(0, rows)

        # Partition dataset based on best question
        true_rows, false_rows = self.partition( rows, question )

        # Build the true branch via recursion
        true_branch = self.build( true_rows )

        # Build the false branch via recursion
        false_branch = self.build( false_rows )

        # Return the Decision node, with references to question and branchs
        return Node(1, None, question, true_branch, false_branch)


    def score(self, x, y):
        n = len(x)
        correct = 0;
        for i in range(n):
            if self.classify( x[i] , self.root_node ) == y[i]:
                correct += 1
        return correct / n

    def predict( self, x, y):
        n = len(x)
        correct = 0;
        for i in range(n):
            if self.classify( x[i] , self.root_node ) == y[i]:
                correct += 1

        print( "N: %s\tC: %s\t%.2f%%" % ( n, correct, ( correct / n * 100 ) ) )

    # used by random forest as a 1 to 1
    def random_forest_predict(self, x):
        y_preds = []
        for i in range( len(x) ):
            y_preds.append( self.classify( x[i], self.root_node ) )
        return y_preds

    def classify( self, row, node):

        # Base Case: Leaf!
        if node.is_decision is 0:
            return node.top_pick()

        if node.question.match(row):
            # True! Look down the true branch
            return self.classify(row, node.true_branch)
        else:
            # False! Look down the true branch
            return self.classify(row, node.false_branch)



class RandomForest():

    """
    Random Forest classifier. Uses a collection of classification trees that
    trains on random subsets of the data using a random subsets of the features.
    Parameters:
    """
    def __init__( self, n_trees=10, max_features=None, stopping_criteria = 0):
        self.n_trees = n_trees
        self.max_features = max_features
        self.stopping_criteria = stopping_criteria

        # Initialize decision trees
        self.the_forest = []
        for tree in range(n_trees):
            self.the_forest.append(Tree())


    # Methods to match skilearn interface specification
    def get_params(self, deep=True):
        return {
            "n_trees": self.n_trees,
            "max_features": self.max_features,
            "stopping_criteria": self.stopping_criteria
        }

    # Methods to match skilearn interface specification
    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self


    def fit( self, x, y ):
        n_features = np.shape(x)[1]
        if not self.max_features:
            self.max_features = int( np.sqrt( n_features ) )

        # Choose one random subset of the data for each tree
        subsets = get_random_subsets( x, y, self.n_trees )

        for i in range( self.n_trees ):
            x_subset, y_subset = subsets[i]

            # Feature bagging (select random subsets of the features)
            idx = np.random.choice( range( n_features ), size=self.max_features, replace=True )

            # Save the indices of the features for prediction
            self.the_forest[i].feature_indices = idx

            # Choose the features corresponding to the indices
            x_subset = x_subset[:, idx]

            # Fit the tree to the data
            self.the_forest[i].fit( x_subset, y_subset, stopping_criteria = self.stopping_criteria )

    def predict( self, x):

        # Height number of samples, width number of trees
        predictions = np.empty( ( x.shape[0], len( self.the_forest ) ) )

        # Let each tree make a prediction on the data
        for i, tree in enumerate( self.the_forest ):
            # Indices of the features that the tree has trained on
            idx = tree.feature_indices

            prediction = tree.random_forest_predict( x[:, idx] )

            predictions[:, i] = prediction

        predictions = np.array(predictions)



        top_voted = np.empty( predictions.shape[0] )

        # We vote!
        for i in range( len( predictions ) ):
            votes = np.unique(predictions[i], return_counts=True )
            if len( votes[0] ) == 1: # all Trees agree on one class
                top_class = votes[0][0];
            else:
                top_class_votes = 0
                top_class_index = 0
                for j in range( len( votes[1] ) ):
                    if votes[1][j] > top_class_votes:
                        top_class_votes = votes[1][j]
                        top_class_index = j

                top_class = votes[0][top_class_index]
            top_voted[i] = top_class

        return top_voted




    def score( self, x, y):
        predictions = self.predict( x )
        n = len(x)
        correct = 0;
        for i in range(n):
            if predictions[i] == y[i]:
                correct += 1

        return correct / n



if __name__ == '__main__':
    #dataset = load_breast_cancer()
    dataset = load_iris()
    #dataset = load_wine()
    #dataset = load_digits()

    #x_train, x_test, y_train, y_test = train_test_split(dataset.data, dataset.target, test_size=0.1)

    #forest = RandomForest()
    #forest.fit(x_train, y_train)

    #forest.score(x_test, y_test)

    for i in range(10):
        if i % 3 == 0:
            print("")
            clf = RandomForest()
            who = "RF"
        elif i % 3 == 1:
            clf = Tree()
            who = "DT"
        else:
            clf = DecisionTreeClassifier()
            clf.set_params
            who = "SK"

        samples = 50
        cv = ShuffleSplit(n_splits= samples, test_size=0.2)
        tic = time.clock()
        scores = cross_val_score(clf, dataset.data, dataset.target, cv=cv)
        toc = time.clock()
        # print(scores)
        print("%s. Accuracy: %0.2f (+/- %0.2f) Time: %0.4f" % (who, scores.mean(), scores.std() * 2, ( toc - tic) /samples ))
