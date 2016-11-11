#!/bin/bash -e

SRC="Blank"
DST="English"

#rm -rf $DST

for i in `ls $SRC`
do
   l="0"
   cp $SRC/$i tmp1
   while read r
   do
      if [ "${#l}" -eq "1" ]
      then
         ll="0$l"
      else
         ll=$l
      fi
      echo "s#@$ll#$r#g"
      cat tmp1 | sed "s#@$ll#$r#g" > tmp2
      mv tmp2 tmp1
      l=$((l+1))
   done < $DST.cnv
   mv tmp1 $DST/$i
done

