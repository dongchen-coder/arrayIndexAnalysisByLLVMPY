; ModuleID = 'gpuRaceDetection'

define void @region_copy(i32 %block_id, i32 %tid, i8* %orig_copy, i32 %size, i8* %new_copy, i8* %union_copy) {
entry:
  %0 = alloca i32, align 4
  %1 = alloca i32, align 4
  %2 = alloca i8*, align 8
  %3 = alloca i32, align 4
  %4 = alloca i8*, align 8
  %5 = alloca i8*, align 8
  store i32 %block_id, i32* %0
  store i32 %tid, i32* %1
  store i8* %orig_copy, i8** %2
  store i32 %size, i32* %3
  store i8* %new_copy, i8** %4
  store i8* %union_copy, i8** %5
  %6 = load i32* %1
  %7 = load i8** %4
  %8 = load i8** %2
  %9 = load i32* %3
  call void @warp_level_parallel_memcpy(i32 %6, i8* %7, i8* %8, i32 %9)
  ret void
}

define void @warp_level_parallel_memcpy(i32 %tid, i8* %dst, i8* %src, i32 %size) {
entry:
  %0 = alloca i32
  %1 = alloca i8*, align 8
  %2 = alloca i8*, align 8
  %3 = alloca i32, align 4
  %opt_dst = alloca i32*, align 8
  %opt_src = alloca i32*, align 8
  %opt_size = alloca i32, align 4
  %ttid = alloca i32, align 4
  %k = alloca i32, align 4
  %idx = alloca i32, align 4
  store i32 %tid, i32* %0
  store i8* %dst, i8** %1
  store i8* %src, i8** %2
  store i32 %size, i32* %3
  %4 = load i8** %1
  %5 = bitcast i8* %4 to i32*
  store i32* %5, i32** %opt_dst
  %6 = load i8** %2
  %7 = bitcast i8* %6 to i32*
  store i32* %7, i32** %opt_src
  %8 = load i32* %3
  %9 = sext i32 %8 to i64
  %10 = udiv i64 %9, 4
  %11 = trunc i64 %10 to i32
  store i32 %11, i32* %opt_size
  %12 = load i32* %0
  %13 = srem i32 %12, 16
  store i32 %13, i32* %ttid
  store i32 0, i32* %k
  br label %blk_15

blk_15:                                           ; preds = %blk_40, %entry
  %14 = load i32* %k
  %15 = load i32* %opt_size
  %16 = sdiv i32 %15, 16
  %17 = add nsw i32 %16, 1
  %18 = icmp slt i32 %14, %17
  br i1 %18, label %blk_21, label %blk_43

blk_21:                                           ; preds = %blk_15
  %19 = load i32* %ttid
  %20 = load i32* %k
  %21 = mul nsw i32 16, %20
  %22 = add nsw i32 %19, %21
  store i32 %22, i32* %idx
  %23 = load i32* %idx
  %24 = load i32* %opt_size
  %25 = icmp slt i32 %23, %24
  br i1 %25, label %blk_29, label %blk_39

blk_29:                                           ; preds = %blk_21
  %26 = load i32* %idx
  %27 = sext i32 %26 to i64
  %28 = load i32** %opt_src
  %29 = getelementptr i32* %28, i64 %27
  %30 = load i32* %29
  %31 = load i32* %idx
  %32 = sext i32 %31 to i64
  %33 = load i32** %opt_dst
  %34 = getelementptr i32* %33, i64 %32
  store i32 %30, i32* %34
  br label %blk_39

blk_39:                                           ; preds = %blk_29, %blk_21
  br label %blk_40

blk_40:                                           ; preds = %blk_39
  %35 = load i32* %k
  %36 = add i32 %35, 1
  store i32 %36, i32* %k
  br label %blk_15

blk_43:                                           ; preds = %blk_15
  call void @__syncthreads()
  ret void
}

declare void @__syncthreads()
