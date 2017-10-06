#!/usr/bin/env bash

# This script downloads the AudioSet subset files, splits them if need be, and
# sets up the folder hierarchy
#
#

# URLs to subset files
EVAL_URL='http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/eval_segments.csv';
BALANCED_TRAIN_URL='http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/balanced_train_segments.csv';
UNBALANCED_TRAIN_URL='http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/unbalanced_train_segments.csv';

# Get script args
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        -s|--split)
        SPLIT="$2"
        shift # past argument
        shift # past value
        ;;
        *)    # unknown option
        POSITIONAL+=("$1") # save it in an array for later
        shift # past argument
        ;;
    esac
    done
    set -- "${POSITIONAL[@]}" # restore positional parameters

    if [ "${#POSITIONAL[@]}" -gt "1" ]; then
        echo "Too many postional arguments";
        exit -1;
    else if [ "${#POSITIONAL[@]}" = "0" ]; then
        echo "Must provide target data directory.";
        exit -1;
    fi
fi

DATASET_DIR=$POSITIONAL;


DATA_DIR="$DATASET_DIR/data"
mkdir -p $DATASET_DIR;
mkdir -p $DATA_DIR;

function process_subset () {
    # Get function arguments
    SUBSET_URL=$1;
    TARGET_DATASET_DIR=$2;
    TARGET_DATA_DIR=$3;
    NUM_SPLIT=$4;


    # Get the name of the subset file and the target filepath
    SUBSET_FNAME="$(basename ${SUBSET_URL})";
    SUBSET_PATH="$TARGET_DATASET_DIR/$SUBSET_FNAME";

    # Get the name of the subset and the subset directory where video and audio will go
    SUBSET_NAME="${SUBSET_FNAME%.*}";
    SUBSET_DIR="$TARGET_DATA_DIR/$SUBSET_NAME";

    echo "Downloading $SUBSET_NAME...";

    # Create the subset directory
    mkdir -p $SUBSET_DIR;

    # Download the subset file if it doesn't exist locally
    wget -nc -O $SUBSET_PATH $SUBSET_URL;

    if [ "$NUM_SPLIT" != "" ]; then
        # Split the subset file into roughly equal sized files
        # Truncate the first few lines
        TRUNC_SUBSET_PATH="$SUBSET_PATH.trunc";

        # Remove the header from the file
        tail -n +4 $SUBSET_PATH > $TRUNC_SUBSET_PATH;

        # Figure out (max) number of lines per file
        TOTAL_NUM_LINES=$(cat $TRUNC_SUBSET_PATH | wc -l);
        LINES_PER_FILE=$(( ($TOTAL_NUM_LINES + $NUM_SPLIT - 1) / $NUM_SPLIT ));

        # Split the subset file into roughly equal sized files. Each will have a
        # numeric prefix '.<num>' with a leading zero if necessary.
        split --lines=$LINES_PER_FILE --numeric-suffixes=1 $TRUNC_SUBSET_PATH "$SUBSET_PATH.";

        # Cleanup
        rm $TRUNC_SUBSET_PATH;
    fi

}

process_subset $EVAL_URL $DATASET_DIR $DATA_DIR $SPLIT;
process_subset $BALANCED_TRAIN_URL $DATASET_DIR $DATA_DIR $SPLIT;
process_subset $UNBALANCED_TRAIN_URL $DATASET_DIR $DATA_DIR $SPLIT;

exit 0;
