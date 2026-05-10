# Heic To Jpg

- Heic 파일을 jpg로 일괄 변경해주는 Python Tkinter 프로그램
- Bg: 윈도우에서 아이폰으로 찍은 사진원본을 구글포토에 업로드하고 해당 파일을 다운로드 받았을때 일괄적으로 HEIC를 JPG로 변경할때 일괄적으로 포맷을 변경하기위해 프로그램작성

![스크린샷 2024-05-21 004855](https://github.com/hwanyeong-choi/heicTojpg_python_tkinter/assets/47169718/d40c2ddd-9911-409b-a32e-08a80c802aa9)

### HeicToJpg 다운로드
HeicToJpg windows [파일 다운로드](https://github.com/hwanyeong-choi/heicTojpg_python_tkinter/releases/tag/v1.0.0)

HeicToJpg windows exe 파일 체크섬[SHA256]
8DCA1A74D153497C4C14510E476EB6AE2471C7CC641A3388DC0AAE479950FC8E 


# 패치 리스트
  - 2024-04-17: Heic to Jpg파일 변환시 exif정보는 누락되어 저장되던 문제 해소
  - 2024-04-18: Heic to Jpg파일 변환시 iccProfile이 누락되어 저장되던 문제 해소
  - 2024-05-21: v1
    1. 별도로 저장경로를 선택하는것이 아닌 heic파일이 존재하는 폴더에 jpg 폴더를 생성하여 변환된 jpg파일을 저장하도록 구현
    2. 파일 리스트에서 파일 선택시 선택한 사진을 미리볼 수 있도록 구현
    3. JPEG, PNG 파일타입을 지정하여 변환할 수 있도록 수정
    4. 멀티 스레드 환경에서 변환을 진행하도록 수정
  - 2026-05-10: v1.1
    1. 간헐적으로 프로그램이 멈추거나 변환이 안 되는 버그 수정
    2. 사진 미리보기 딜레이 현상 개선 (로딩 속도 최적화)

# 사용법 Youtube
  [![Video Label](http://img.youtube.com/vi/oybSIMjcYbM/0.jpg)](https://youtu.be/oybSIMjcYbM)
