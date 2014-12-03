; ModuleID = 'matrixMul.c'
target datalayout = "e-m:o-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-apple-macosx10.10.0"

%struct.threeType = type { i32, i32, i32 }

@blockIdx = common global %struct.threeType zeroinitializer, align 4
@threadIdx = common global %struct.threeType zeroinitializer, align 4

; Function Attrs: nounwind ssp uwtable
define void @__syncthreads() #0 {
  ret void
}

; Function Attrs: nounwind ssp uwtable
define void @matrixMulCUDA(float* %C, float* %A, float* %B, i32 %wA, i32 %wB) #0 {
  %1 = alloca float*, align 8
  %2 = alloca float*, align 8
  %3 = alloca float*, align 8
  %4 = alloca i32, align 4
  %5 = alloca i32, align 4
  %bx = alloca i32, align 4
  %by = alloca i32, align 4
  %tx = alloca i32, align 4
  %ty = alloca i32, align 4
  %aBegin = alloca i32, align 4
  %aEnd = alloca i32, align 4
  %aStep = alloca i32, align 4
  %bBegin = alloca i32, align 4
  %bStep = alloca i32, align 4
  %Csub = alloca float, align 4
  %a = alloca i32, align 4
  %b = alloca i32, align 4
  %As = alloca [32 x [32 x float]], align 16
  %Bs = alloca [32 x [32 x float]], align 16
  %k = alloca i32, align 4
  %c = alloca i32, align 4
  store float* %C, float** %1, align 8
  store float* %A, float** %2, align 8
  store float* %B, float** %3, align 8
  store i32 %wA, i32* %4, align 4
  store i32 %wB, i32* %5, align 4
  %6 = load i32* getelementptr inbounds (%struct.threeType* @blockIdx, i32 0, i32 0), align 4
  store i32 %6, i32* %bx, align 4
  %7 = load i32* getelementptr inbounds (%struct.threeType* @blockIdx, i32 0, i32 1), align 4
  store i32 %7, i32* %by, align 4
  %8 = load i32* getelementptr inbounds (%struct.threeType* @threadIdx, i32 0, i32 0), align 4
  store i32 %8, i32* %tx, align 4
  %9 = load i32* getelementptr inbounds (%struct.threeType* @threadIdx, i32 0, i32 1), align 4
  store i32 %9, i32* %ty, align 4
  %10 = load i32* %4, align 4
  %11 = mul nsw i32 %10, 32
  %12 = load i32* %by, align 4
  %13 = mul nsw i32 %11, %12
  store i32 %13, i32* %aBegin, align 4
  %14 = load i32* %aBegin, align 4
  %15 = load i32* %4, align 4
  %16 = add nsw i32 %14, %15
  %17 = sub nsw i32 %16, 1
  store i32 %17, i32* %aEnd, align 4
  store i32 32, i32* %aStep, align 4
  %18 = load i32* %bx, align 4
  %19 = mul nsw i32 32, %18
  store i32 %19, i32* %bBegin, align 4
  %20 = load i32* %5, align 4
  %21 = mul nsw i32 32, %20
  store i32 %21, i32* %bStep, align 4
  store float 0.000000e+00, float* %Csub, align 4
  %22 = load i32* %aBegin, align 4
  store i32 %22, i32* %a, align 4
  %23 = load i32* %bBegin, align 4
  store i32 %23, i32* %b, align 4
  br label %24

; <label>:24                                      ; preds = %88, %0
  %25 = load i32* %a, align 4
  %26 = load i32* %aEnd, align 4
  %27 = icmp sle i32 %25, %26
  br i1 %27, label %28, label %95

; <label>:28                                      ; preds = %24
  %29 = load i32* %a, align 4
  %30 = load i32* %4, align 4
  %31 = load i32* %ty, align 4
  %32 = mul nsw i32 %30, %31
  %33 = add nsw i32 %29, %32
  %34 = load i32* %tx, align 4
  %35 = add nsw i32 %33, %34
  %36 = sext i32 %35 to i64
  %37 = load float** %2, align 8
  %38 = getelementptr inbounds float* %37, i64 %36
  %39 = load float* %38, align 4
  %40 = load i32* %tx, align 4
  %41 = sext i32 %40 to i64
  %42 = load i32* %ty, align 4
  %43 = sext i32 %42 to i64
  %44 = getelementptr inbounds [32 x [32 x float]]* %As, i32 0, i64 %43
  %45 = getelementptr inbounds [32 x float]* %44, i32 0, i64 %41
  store float %39, float* %45, align 4
  %46 = load i32* %b, align 4
  %47 = load i32* %5, align 4
  %48 = load i32* %ty, align 4
  %49 = mul nsw i32 %47, %48
  %50 = add nsw i32 %46, %49
  %51 = load i32* %tx, align 4
  %52 = add nsw i32 %50, %51
  %53 = sext i32 %52 to i64
  %54 = load float** %3, align 8
  %55 = getelementptr inbounds float* %54, i64 %53
  %56 = load float* %55, align 4
  %57 = load i32* %tx, align 4
  %58 = sext i32 %57 to i64
  %59 = load i32* %ty, align 4
  %60 = sext i32 %59 to i64
  %61 = getelementptr inbounds [32 x [32 x float]]* %Bs, i32 0, i64 %60
  %62 = getelementptr inbounds [32 x float]* %61, i32 0, i64 %58
  store float %56, float* %62, align 4
  call void @__syncthreads()
  store i32 0, i32* %k, align 4
  br label %63

; <label>:63                                      ; preds = %84, %28
  %64 = load i32* %k, align 4
  %65 = icmp slt i32 %64, 32
  br i1 %65, label %66, label %87

; <label>:66                                      ; preds = %63
  %67 = load i32* %k, align 4
  %68 = sext i32 %67 to i64
  %69 = load i32* %ty, align 4
  %70 = sext i32 %69 to i64
  %71 = getelementptr inbounds [32 x [32 x float]]* %As, i32 0, i64 %70
  %72 = getelementptr inbounds [32 x float]* %71, i32 0, i64 %68
  %73 = load float* %72, align 4
  %74 = load i32* %tx, align 4
  %75 = sext i32 %74 to i64
  %76 = load i32* %k, align 4
  %77 = sext i32 %76 to i64
  %78 = getelementptr inbounds [32 x [32 x float]]* %Bs, i32 0, i64 %77
  %79 = getelementptr inbounds [32 x float]* %78, i32 0, i64 %75
  %80 = load float* %79, align 4
  %81 = fmul float %73, %80
  %82 = load float* %Csub, align 4
  %83 = fadd float %82, %81
  store float %83, float* %Csub, align 4
  br label %84

; <label>:84                                      ; preds = %66
  %85 = load i32* %k, align 4
  %86 = add nsw i32 %85, 1
  store i32 %86, i32* %k, align 4
  br label %63

; <label>:87                                      ; preds = %63
  call void @__syncthreads()
  br label %88

; <label>:88                                      ; preds = %87
  %89 = load i32* %aStep, align 4
  %90 = load i32* %a, align 4
  %91 = add nsw i32 %90, %89
  store i32 %91, i32* %a, align 4
  %92 = load i32* %bStep, align 4
  %93 = load i32* %b, align 4
  %94 = add nsw i32 %93, %92
  store i32 %94, i32* %b, align 4
  br label %24

; <label>:95                                      ; preds = %24
  %96 = load i32* %5, align 4
  %97 = mul nsw i32 %96, 32
  %98 = load i32* %by, align 4
  %99 = mul nsw i32 %97, %98
  %100 = load i32* %bx, align 4
  %101 = mul nsw i32 32, %100
  %102 = add nsw i32 %99, %101
  store i32 %102, i32* %c, align 4
  %103 = load float* %Csub, align 4
  %104 = load i32* %c, align 4
  %105 = load i32* %5, align 4
  %106 = load i32* %ty, align 4
  %107 = mul nsw i32 %105, %106
  %108 = add nsw i32 %104, %107
  %109 = load i32* %tx, align 4
  %110 = add nsw i32 %108, %109
  %111 = sext i32 %110 to i64
  %112 = load float** %1, align 8
  %113 = getelementptr inbounds float* %112, i64 %111
  store float %103, float* %113, align 4
  ret void
}

attributes #0 = { nounwind ssp uwtable "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = metadata !{metadata !"Apple LLVM version 6.0 (clang-600.0.54) (based on LLVM 3.5svn)"}
