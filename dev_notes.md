Sample bash status log with error notes on 900-page book

```bash
Finding page delivery service identifier...
9752507
Fetching metadata from LibraryCloud...
990014230180203941
Scientific papers of Asa Gray
Getting page count...
940
Getting book contents...
Collecting 940 page IDs
  0%|          | 0/940 [00:00<?, ?it/s]Page  108  (id: 9754495 ) returned html
 19%|#9        | 183/940 [00:18<10:58,  1.15it/s]
 Page  184  (id: 9754571 ) returned html
 22%|##2       | 211/940 [00:30<10:33,  1.15it/s]
 Page  212  (id: 9754599 ) returned html
 27%|##7       | 255/940 [00:42<02:38,  4.33it/s]
 Page  256  (id: 9754643 ) returned html
 31%|###1      | 292/940 [00:49<02:09,  5.01it/s]
 Page  293  (id: 9754680 ) returned html
 53%|#####3    | 500/940 [01:34<06:48,  1.08it/s]
 Page  501  (id: 9754888 ) returned html
 58%|#####8    | 548/940 [01:46<01:17,  5.03it/s]
 Page  549  (id: 9754936 ) returned html
 63%|######3   | 596/940 [01:57<01:15,  4.56it/s]
 Page  597  (id: 9754984 ) returned html
 67%|######7   | 632/940 [02:08<01:26,  3.54it/s]
 Page  633  (id: 9755020 ) returned html
 94%|#########4| 888/940 [03:04<00:10,  4.76it/s]
 Page  889  (id: 9755276 ) returned html
100%|##########| 940/940 [03:14<00:00,  4.76it/s]
Creating JSON file for metadata...
Creating text file from OCR...
Done! Check results folder.
```

Another example after putting in a catch-and-try-again loop for html error pages 
```bash
Finding digital repository service identifier...
9752507
Getting metadata from LibraryCloud...
Scientific papers of Asa Gray
Getting page count...
940
Counting page IDs...
940
Getting book contents...
 20%|##        | 192/940 [00:53<02:35,  4.82it/s]
Page  193  (id: 9754580 ) returned html
 24%|##3       | 224/940 [01:06<02:17,  5.21it/s]
Page  225  (id: 9754612 ) returned html
 28%|##7       | 262/940 [01:21<02:08,  5.28it/s]
Page  263  (id: 9754650 ) returned html
 44%|####3     | 409/940 [02:00<07:47,  1.14it/s]
Page  410  (id: 9754797 ) returned html
 46%|####5     | 432/940 [02:11<01:46,  4.78it/s]
Page  433  (id: 9754820 ) returned html
 49%|####8     | 457/940 [02:22<02:16,  3.54it/s]
Page  458  (id: 9754845 ) returned html
 51%|#####1    | 484/940 [02:32<01:24,  5.39it/s]
Page  485  (id: 9754872 ) returned html
 72%|#######2  | 680/940 [03:26<00:49,  5.29it/s]
Page  681  (id: 9755068 ) returned html
 75%|#######5  | 706/940 [03:37<00:42,  5.51it/s]
Page  707  (id: 9755094 ) returned html
 78%|#######8  | 735/940 [03:48<00:40,  5.11it/s]
Page  736  (id: 9755123 ) returned html
 81%|########1 | 762/940 [03:59<00:37,  4.70it/s]
Page  763  (id: 9755150 ) returned html
100%|#########9| 936/940 [04:47<00:00,  4.81it/s]
Page  937  (id: 9755324 ) returned html
100%|##########| 940/940 [04:52<00:00,  1.38it/s]
Creating JSON file for metadata...
Creating text file from OCR...
Done! Check results folder.
```
