import tensorflow as tf
import numpy as np
from tensorflow.examples.tutorials.mnist import input_data


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


'''

tfrecords作为tensorflow的数据io格式，可以解决大数据集爆内存问题，一边读入数据，一边
feed数据

'''
def get_batches(filenamequeue, batch_size, nclass, shuffle):
    '''
    param：
          filenamequene：文件队列
          batch_size：
          nclass： 类别数
          shuffle：随机打乱，只对训练集
    return：
          image_batch, label_batch  返回tensor

    '''
    reader = tf.TFRecordReader()
    filename_queue = tf.train.string_input_producer([filenamequeue])
    _, serialized_example = reader.read(filename_queue)

    features = tf.parse_single_example(serialized_example,
                                       features={
                                           'image_raw': tf.FixedLenFeature([],tf.string),
                                           'label': tf.FixedLenFeature([], tf.int64),
                                           'width': tf.FixedLenFeature([], tf.int64),
                                           'height': tf.FixedLenFeature([], tf.int64)
                                       })

    image = tf.decode_raw(features['image_raw'], tf.uint8)
    label = tf.cast(features['label'], tf.int64)
    width = tf.cast(features['width'], tf.int64)
    height= tf.cast(features['height'], tf.int64)

    im_shape = tf.stack([28, 28, 1])
    image = tf.reshape(image, im_shape)
    label = tf.reshape(label, [1])
    min_after_dequeue = 10000
    capacity = min_after_dequeue + 3*batch_size
    if shuffle:
        image_batch,label_batch = tf.train.shuffle_batch(
                                    [image, label],
                                    batch_size = batch_size,
                                    capacity = capacity,
                                    min_after_dequeue = min_after_dequeue,
                                    num_threads = 4)

    else:
        image_batch, label_batch = tf.train.batch(
                                      [image, label],
                                      batch_size = batch_size,
                                      num_threads = 4,
                                      capacity = 1000)
    label_batch = tf.one_hot(label_batch, depth = nclass)
    label_batch = tf.cast(label_batch, dtype=tf.int32)
    label_batch = tf.reshape(label_batch, [batch_size, nclass])

    return image_batch, label_batch

def parse_example(serialized_example,nclass=10):
    '''

    param:
          serialized_example: 序列化的数据
          nclass: 类别数
    return:
           image，label 单样本的tensor
    '''
    features = tf.parse_single_example(serialized_example,
                                       features={
                                           'image_raw': tf.FixedLenFeature([], tf.string),
                                           'label': tf.FixedLenFeature([], tf.int64),
                                           'width': tf.FixedLenFeature([], tf.int64),
                                           'height': tf.FixedLenFeature([], tf.int64)
                                       })

    image = tf.decode_raw(features['image_raw'], tf.uint8)
    label = tf.cast(features['label'], tf.int32)
    width = tf.cast(features['width'], tf.int64)
    height= tf.cast(features['height'], tf.int64)

    im_shape = tf.stack([28, 28, 1])
    image = tf.reshape(image, im_shape)
    label = tf.one_hot(label, depth=nclass)
    return image, label


def get_batches_v1(filenames, batchsize, nclass, shuffle=True):
    '''

    param:
          filenames: tfrecords文件路径
          batchsize:
          nclass:
          shuffle: 是否随机打乱
    return:
          返回数据迭代器iterator，这里使用可初始化的iterator
    '''
    dataset = tf.data.TFRecordDataset([filenames])
    #这里使用lambda使得map支持带参数的函数作为输入参数
    dataset = dataset.map(lambda x: parse_example(x, nclass=10))
    if shuffle:
        # 这里不使用repeat，因为使用repeat函数，每个epoch的起止没有标志，难以界定epoch的起止
        dataset = dataset.shuffle(buffer_size=10000).batch(batchsize)
    else:
        dataset = dataset.batch(batchsize)

    iterator = dataset.make_initializable_iterator()
    return iterator


def get_batches_v2(train_set, val_set, batchsize, nclass):
    '''

    param
         train_set: 训练集path
         val_set: 验证集path
         batchsize:
         nclass:

    return:
          train_init_op 训练集迭代器初始化操作
          val_init_op   验证集迭代器初始化操作
          iterator      可重新新初始化迭代器

    '''

    train_dataset = tf.data.TFRecordDataset([train_set])
    val_dataset   = tf.data.TFRecordDataset([val_set])

    train_dataset = train_dataset.map(lambda x: parse_example(x, nclass=10))
    val_dataset = val_dataset.map(lambda x: parse_example(x, nclass=10))

    train_dataset = train_dataset.shuffle(buffer_size=10000).batch(batchsize)
    val_dataset = val_dataset.batch(batchsize)

    iterator = tf.data.Iterator.from_structure(train_dataset.output_types,
                                               train_dataset.output_shapes)
    train_init_op = iterator.make_initializer(train_dataset)
    val_init_op = iterator.make_initializer(val_dataset)

    return train_init_op, val_init_op, iterator


def get_batches_v3(train_set, val_set, batchsize, nclass):

    train_dataset = tf.data.TFRecordDataset([train_set])
    val_dataset = tf.data.TFRecordDataset([val_set])

    train_dataset = train_dataset.map(lambda x: parse_example(x, nclass=10))
    val_dataset = val_dataset.map(lambda x: parse_example(x, nclass=10))

    train_dataset = train_dataset.shuffle(buffer_size=10000).batch(batchsize)
    val_dataset = val_dataset.batch(batchsize)

    handle = tf.placeholder(tf.string, shape=[])
    iterator = tf.data.Iterator.from_string_handle(
        handle, train_dataset.output_types, train_dataset.output_shapes)

    train_iterator = train_dataset.make_initializable_iterator()
    val_iterator = val_dataset.make_initializable_iterator()

    return handle, train_iterator, val_iterator, iterator

def get_batches_v4(train_set, val_set, batchsize, nclass, epoches):

    train_dataset = tf.data.TFRecordDataset([train_set])
    val_dataset = tf.data.TFRecordDataset([val_set])

    train_dataset = train_dataset.map(lambda x: parse_example(x, nclass=10))
    val_dataset = val_dataset.map(lambda x: parse_example(x, nclass=10))

    train_dataset = train_dataset.shuffle(buffer_size=10000).repeat(epoches).batch(batchsize)

    val_dataset = val_dataset.repeat(epoches).batch(batchsize)

    train_iterator = train_dataset.make_one_shot_iterator()
    val_iterator = val_dataset.make_one_shot_iterator()

    return train_iterator, val_iterator

def write_tfrecords(filename, is_train):

    mnist = input_data.read_data_sets("./mnist_data/",dtype=tf.uint8, one_hot=True)

    if is_train:
       images = mnist.train.images
       labels = mnist.train.labels
       pixels = images.shape[0]
       num_examples = mnist.train.num_examples
    else:
       images = mnist.test.images
       labels = mnist.test.labels
       pixels = images.shape[0]
       num_examples = mnist.test.num_examples
    image_height= 28
    image_width = 28

    writer = tf.python_io.TFRecordWriter(filename)
    for index in range(num_examples):
        image_raw = images[index].tostring()
        example = tf.train.Example(features=tf.train.Features(feature={
            'label': _int64_feature(np.argmax(labels[index])),
            'image_raw': _bytes_feature(image_raw),
            'width': _int64_feature(image_width),
            'height': _int64_feature(image_height)}))
        writer.write(example.SerializeToString())

    writer.close()



