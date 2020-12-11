#!/bin/bash

#
# start with -f option to only process the first file found
#

MODEL="EwE_benguela"

BASE_DIR="/work/bb0820/ISIMIP/ISIMIP3b/UploadArea/marine-fishery_regional"

module load python/3.5.2
module load git

if [ ! -d isimip-protocol-3 ];then
  git clone https://github.com/ISI-MIP/isimip-protocol-3
else
  cd isimip-protocol-3
  git pull origin
  cd ..
fi

echo

# convert all csv files
python convert.py $@ -m $MODEL -b $BASE_DIR

#exit

echo;echo "process files to _tmp folder..."
for FILE in $BASE_DIR/$MODEL/convert2nc/netcdf/*.nc;do
  GCM=$(basename $FILE | cut -d_ -f2)
  CLIM_EXP=$(basename $FILE | cut -d_ -f4)
  YEAR_START=$(basename $FILE .nc| cut -d_ -f10)
  YEAR_END=$(basename $FILE .nc| cut -d_ -f11)

  if [ $YEAR_START -le 2014 ];then
    PERIOD="historical"

    if [ $CLIM_EXP != 'picontrol' ] && [ $CLIM_EXP != $PERIOD ];then
      CLIM_FILE_NEW="historical"
    else
      CLIM_FILE_NEW=$CLIM_EXP
    fi

    if [ $YEAR_END -le 2014 ];then
      # copy
      echo "move historical file ($(basename $FILE))"
      cp $FILE $BASE_DIR/$MODEL/_tmp/$GCM/$PERIOD/
    else
      # extract
      echo "extract historical data from file $(basename $FILE)"
      cdo -s --history -f nc4c -z zip -selyear,$YEAR_START/2014 \
          $FILE \
          $BASE_DIR/$MODEL/_tmp/$GCM/$PERIOD/$(basename $FILE | sed s/$YEAR_END/2014/ | sed s/$CLIM_EXP/$CLIM_FILE_NEW/)
    fi
  fi

  if [ $YEAR_END -ge 2015 ];then
    PERIOD="future"
    if [ $YEAR_START -ge 2015 ];then
      # copy
      echo "move future file $(basename $FILE)"
      cp $FILE $BASE_DIR/$MODEL/_tmp/$GCM/$PERIOD/
    else
      # extract
      echo "extract future data from file $(basename $FILE)"
      cdo -s --history -f nc4c -z zip -selyear,2015/$YEAR_END \
          $FILE \
          $BASE_DIR/$MODEL/_tmp/$GCM/$PERIOD/$(basename $FILE | sed s/$YEAR_START/2015/)
    fi
  fi
  rm $FILE
done

echo;echo "done"
