# version: 1.0

import numpy as np
from collections import deque
import dsp
from dsp.doppler_processing import doppler_processing
import dsp.range_processing as range_processing
import dsp.angle_estimation as Angle_dsp
import dsp.utils as utils
import dsp.compensation as Compensation
from dsp.utils import Window
import globalvar as gl


rti_queue = deque(maxlen=12)
rdi_queue = deque(maxlen=12)
rai_queue = deque(maxlen=12)
rei_queue = deque(maxlen=12)

gesturetimecnt = 0
# 用于计数手悬停事件

gesturetimecnt2 = 0

NUM_TX = 3
NUM_RX = 4
VIRT_ANT = 4
VIRT_ANT1 = 1
# Data specific parameters
NUM_CHIRPS = 64
NUM_ADC_SAMPLES = 64
RANGE_RESOLUTION = .0488
DOPPLER_RESOLUTION = 0.0806
NUM_FRAMES = 300

# DSP processing parameters
SKIP_SIZE = 4  # 忽略边缘角度的目标
ANGLE_RES = 2  # 角度分辨率
ANGLE_RANGE = 90  # 监督范围
ANGLE_FFT_BINS= 64
ANGLE_BINS = (ANGLE_RANGE * 2) // ANGLE_RES + 1
BINS_PROCESSED = 64

numRangeBins = NUM_ADC_SAMPLES
numDopplerBins = NUM_CHIRPS

# 计算分辨率
range_resolution, bandwidth = dsp.range_resolution(NUM_ADC_SAMPLES)
doppler_resolution = dsp.doppler_resolution(bandwidth)

# Start DSP processing
range_azimuth = np.zeros((int(ANGLE_BINS), BINS_PROCESSED))
range_elevation = np.zeros((int(ANGLE_BINS), BINS_PROCESSED))
azimuth_elevation = np.zeros((ANGLE_FFT_BINS, ANGLE_FFT_BINS, NUM_ADC_SAMPLES))

num_vec, steering_vec = Angle_dsp.gen_steering_vec(ANGLE_RANGE, ANGLE_RES, VIRT_ANT) #theta跨度 theta分辨率 Vrx天线信号的数量

def doppler_fft(x,window_type_2d=None):
    
    fft2d_in = np.transpose(x, axes=(1, 0))  # rangbin chirps
    if window_type_2d: 
        fft2d_in = utils.windowing(fft2d_in, window_type_2d, axis=1)

    # 这里用zoom——FTT，是不是更加有效提取有效频率信息呢
    fft2d_out = np.fft.fft(fft2d_in, axis=1)#frame rangbin dopplerbin 
    fft2d_log_abs = np.log2(np.abs(fft2d_out))
    # numADCSamples, numChirpsPerFrame
    det_matrix_vis = np.fft.fftshift(fft2d_log_abs, axes=1)
    return det_matrix_vis
    
# 该函数主要是画三个图 
# RTI
# DTI
# ATI

framecnt  = 0
def RDA_Time(adc_data, window_type_1d=None, clutter_removal_enabled=True, CFAR_enable=False, axis=-1):

    global gesturetimecnt, framecnt
    #  转换成(num_chirps_per_frame, num_rx_antennas, num_adc_samples)
    adc_data = np.transpose(adc_data, [0, 2, 1])
    # radar_cube = range_processing(adc_data, window_type_1d, 2)
    # 2倍抽取 降低dmax
    # radar_cube = range_processing(np.concatenate([adc_data[:,:,0:64:2],adc_data[:,:,0:64:2]], axis=2), window_type_1d, 2)
    radar_cube = range_processing(2*adc_data[:,:,0:64:2], window_type_1d, 2)

    if clutter_removal_enabled:
        radar_cube = Compensation.clutter_removal(radar_cube,axis=0)


    # 距离多普勒图
    range_doppler_fft, aoa_input = doppler_processing(radar_cube, 
                                            num_tx_antennas=3, 
                                            interleaved=False, 
                                            clutter_removal_enabled=False, #前面已经做了
                                            window_type_2d=Window.HANNING,
                                            accumulate = False)
    # (numRangeBins, numVirtualAntennas, num_doppler_bins)

    rdi_abs = np.transpose(np.fft.fftshift(np.abs(range_doppler_fft), axes=2), [0, 2, 1])
    rdi_abs = np.flip(rdi_abs, axis=0)
    rdi_queue.append(rdi_abs)
    # 16个frame叠加返回
    rdi_framearray = np.array(rdi_queue)#frame chirps adcnum numVirtualAntennas
    
    # 角度图：
    # azimuth_elevation[0,0:4,:] = range_doppler_fft[:,[10,8,6,4],0].T
    # azimuth_elevation[1,0:4,:] = range_doppler_fft[:,[11,9,7,5],0].T
    # azimuth_elevation[2,0:2,:] = range_doppler_fft[:,[2,0],0].T
    # azimuth_elevation[3,0:2,:] = range_doppler_fft[:,[3,0],0].T
    # aei_raw = np.fft.fft2(azimuth_elevation, axes=[0, 1])
    # aei_raw = np.log2(np.abs(aei_raw))
    # 。range_doppler_fft
    # 距离时间图
    det_matrix = radar_cube[:, 0, :]

    #用距离图作为判断 
    # [4:36,]是指4~36这个rangbin区间，有true的隔宿大于26个
    Iscapture = gl.get_value('IsRecognizeorCapture')
    # if(np.sum(det_matrix[2:36,:]>3e3)>26) and Iscapture:16
    if(np.sum(det_matrix[:,36:62]>3e3)>14) :
        if Iscapture:
            gesturetimecnt = gesturetimecnt + 1
        # print("有手势%d" %gesturetimecnt)

    if(gesturetimecnt>=2) and Iscapture:
        framecnt = framecnt + 1
        # framecnt是用来相当延迟多少帧再截图到judgegesture文件夹中
        if framecnt>=8:
            # print("进来了")
            # datetime.now()
            # a = datetime.now() #获得当前时间
            if gl.get_value('timer_2s'):
                gl.set_value('usr_gesture',True)    
                gl.set_value('timer_2s',False) 
            # print("有手势")
            framecnt = 0
            gesturetimecnt=0
            

    rti_queue.append(det_matrix)
    rti_framearray = np.array(rti_queue)#frame chirps adcnum
    rti_array = np.reshape(rti_framearray, (1, -1, 64))#chirps adcnum
    # (num_chirps_per_frame, num_range_bins, num_rx_antennas)
    rti_array_out = np.transpose(rti_array, [1, 2, 0])

    # 微多普勒时间图
    micro_doppler_data = np.zeros((rti_framearray.shape[0], rti_framearray.shape[1], rti_framearray.shape[2]), dtype=np.float64)
    micro_doppler_data_out = np.zeros((16,64), dtype=np.float64)
    for i, frame in enumerate(rti_framearray):
            # --- Show output
            det_matrix_vis = doppler_fft(frame,window_type_2d=Window.HANNING)
            micro_doppler_data[i,:,:] = det_matrix_vis

    
    rti_array_out = np.flip(np.abs(rti_array_out), axis=1)
    # 
    rti_array_out[rti_array_out<3e3]=0
    # # 用RDI图判断信噪比强度64*64
    # if(np.sum(rti_array_out[0:1024:16,:,:]<100)>4090):
    #     SNR = False
    # else:
    #     SNR = True

    micro_doppler_data_out = micro_doppler_data.sum(axis=1)

    micro_doppler_data_out[micro_doppler_data_out<20]=0

    return rti_array_out, rdi_framearray, micro_doppler_data_out



def Range_Angle(data,  padding_size=None, clutter_removal_enabled=True, window_type_1d = Window.HANNING,Music_enable = False):
    # (0:TX1-RX1,1:TX1-RX2,2:TX1-RX3,3:TX1-RX4,| 4:TX2-RX1,5:TX2-RX2,6:TX2-RX3,7:TX2-RX4,| 8:TX3-RX1,9:TX3-RX2,10:TX3-RX3,11:TX3-RX4)
    # data = np.fft.fft2(data[:, :, [1,0,9,8]], s=[padding_size[0], padding_size[1]], axes=[0, 1])
    # global SNR

    #  转换成(num_chirps_per_frame, num_rx_antennas, num_adc_samples)
    adc_data = np.transpose(data, [0, 2, 1])
    # radar_cube = dsp.zoom_range_processing(adc_data, 0.1, 0.5, 1, 0, adc_data.shape[2])
    radar_cube = range_processing(2*adc_data[:,:,0:64:3], window_type_1d, 2)

    if clutter_removal_enabled:
        radar_cube = Compensation.clutter_removal(radar_cube,axis=0)

    # np.save('data.npy',radar_cube)
    frame_SNR = np.log(np.sum(np.abs(radar_cube[:,:])))-14.7
    if(np.abs(frame_SNR)<1.8):
        frame_SNR = 0
    # print(frame_SNR)
    # --- capon beamforming
    beamWeights   = np.zeros((VIRT_ANT, BINS_PROCESSED), dtype=np.complex_)

    # Note that when replacing with generic doppler estimation functions, radarCube is interleaved and
    # has doppler at the last dimension.
    # 方位角
    for i in range(BINS_PROCESSED):
        if Music_enable:
            range_azimuth[:,i] = dsp.aoa_music_1D(steering_vec, radar_cube[:, [10,8,6,4], i].T, num_sources=1)
        else:                                                                  #4,6,8,10#
            range_azimuth[:,i], beamWeights[:,i] = dsp.aoa_capon(radar_cube[:, [7,4,3,0], i].T, steering_vec, magnitude=True)
            # range_azimuth[:,i], beamWeights[:,i] = dsp.aoa_capon_new(radar_cube[:, [10,8,6,4], i].T,radar_cube[:, [10,8,6,4], i+1].T, steering_vec, magnitude=True)
    # 俯仰角
    for i in range(BINS_PROCESSED): 
        if Music_enable:
            range_elevation[:,i] = dsp.aoa_music_1D(steering_vec, radar_cube[:, [1,0,9,8], i].T, num_sources=1)
        else:
            # radar_cube[:, [1,0,9,8], i].T*[[1],[-1],[1],[-1]] 不用这个，和导向矢量有关系把
            range_elevation[:,i], beamWeights[:,i] = dsp.aoa_capon(radar_cube[:, [7,6,11,10], i].T*[[1],[-1],[1],[-1]], steering_vec, magnitude=True)

    rdi_ab1 = np.flip(np.abs(range_azimuth), axis=1)
    # rdi_ab2 = np.fft.fftshift(range_elevation, axes=0)
    rdi_ab2 = np.flip(np.abs(range_elevation), axis=1)
    rdi_ab1 = np.minimum(rdi_ab1,rdi_ab1.max()/2)
    rdi_ab2 = np.minimum(rdi_ab2,rdi_ab2.max()/2)
    # 把不在手势范围的目标去除
    rdi_ab1[:,40:90] = 0
    rdi_ab2[:,40:90] = 0
    # rdi_ab1[:,13:19] = 0.1*rdi_ab1[:,13:19] 
    # rdi_ab2[:,13:19] = 0.1*rdi_ab2[:,13:19] 
    # rdi_ab1[:5,:] = 0
    # rdi_ab2[-5:,:] = 0
    # 加权 信噪比
    rdi_ab1 = rdi_ab1 / rdi_ab1.max() * frame_SNR
    rdi_ab2 = rdi_ab2 / rdi_ab2.max() * frame_SNR

    rai_queue.append(rdi_ab1)
    rei_queue.append(rdi_ab2)
    # 16个frame叠加返回
    rai_framearray = np.array(rai_queue)#frame chirps adcnum 
    rei_framearray = np.array(rei_queue)#frame chirps adcnum 

    return rai_framearray, rei_framearray

  