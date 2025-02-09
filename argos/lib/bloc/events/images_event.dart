import 'package:equatable/equatable.dart';

sealed class BaseEvent extends Equatable {
  const BaseEvent();

  @override
  List<Object> get props => [];
}

final class GetImages extends BaseEvent {
  const GetImages();

  @override
  List<Object> get props => [];
}

final class GetImageAnalysis extends BaseEvent {
  final String imageId;

  const GetImageAnalysis(this.imageId);

  @override
  List<Object> get props => [imageId];
}
