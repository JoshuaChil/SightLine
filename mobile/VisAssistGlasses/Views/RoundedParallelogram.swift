//
//  RoundedParallelogram.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/18/25.
//

import SwiftUI

struct RoundedParallelogram: Shape {
    var cornerRadius: CGFloat = 10
    var slantOffset: CGFloat = 20

    func path(in rect: CGRect) -> Path {
        var path = Path()

        // Points for top and bottom slant:
        // Top edge shifted right by slantOffset
        let topLeft = CGPoint(x: rect.minX, y: rect.minY + slantOffset)
        let topRight = CGPoint(x: rect.maxX, y: rect.minY - slantOffset)
        // Bottom edge shifted left by slantOffset
        let bottomRight = CGPoint(x: rect.maxX, y: rect.maxY - slantOffset)
        let bottomLeft = CGPoint(x: rect.minX, y: rect.maxY + slantOffset)

        // Start at topLeft, move right along top edge
        path.move(to: CGPoint(x: topLeft.x + cornerRadius, y: topLeft.y))

        // Top edge line + rounded top-right corner
        path.addLine(to: CGPoint(x: topRight.x - cornerRadius, y: topRight.y))
        path.addArc(center: CGPoint(x: topRight.x - cornerRadius, y: topRight.y + cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: -90),
                    endAngle: Angle(degrees: 0),
                    clockwise: false)

        // Right edge vertical line + rounded bottom-right corner
        path.addLine(to: CGPoint(x: bottomRight.x, y: bottomRight.y - cornerRadius))
        path.addArc(center: CGPoint(x: bottomRight.x - cornerRadius, y: bottomRight.y - cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: 0),
                    endAngle: Angle(degrees: 90),
                    clockwise: false)

        // Bottom edge line + rounded bottom-left corner
        path.addLine(to: CGPoint(x: bottomLeft.x + cornerRadius, y: bottomLeft.y))
        path.addArc(center: CGPoint(x: bottomLeft.x + cornerRadius, y: bottomLeft.y - cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: 90),
                    endAngle: Angle(degrees: 180),
                    clockwise: false)

        // Left edge vertical line + rounded top-left corner
        path.addLine(to: CGPoint(x: topLeft.x, y: topLeft.y + cornerRadius))
        path.addArc(center: CGPoint(x: topLeft.x + cornerRadius, y: topLeft.y + cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: 180),
                    endAngle: Angle(degrees: 270),
                    clockwise: false)

        path.closeSubpath()

        return path
    }
}

struct RoundedParallelogramFlatBottom: Shape {
    var cornerRadius: CGFloat = 10
    var slantOffset: CGFloat = 20

    func path(in rect: CGRect) -> Path {
        var path = Path()

        // Points for top and bottom slant:
        // Top edge shifted right by slantOffset
        let topLeft = CGPoint(x: rect.minX, y: rect.minY + slantOffset)
        let topRight = CGPoint(x: rect.maxX, y: rect.minY - slantOffset)
        // Bottom edge shifted left by slantOffset
        let bottomRight = CGPoint(x: rect.maxX, y: rect.maxY)
        let bottomLeft = CGPoint(x: rect.minX, y: rect.maxY)

        // Start at topLeft, move right along top edge
        path.move(to: CGPoint(x: topLeft.x + cornerRadius, y: topLeft.y))

        // Top edge line + rounded top-right corner
        path.addLine(to: CGPoint(x: topRight.x - cornerRadius, y: topRight.y))
        path.addArc(center: CGPoint(x: topRight.x - cornerRadius, y: topRight.y + cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: -90),
                    endAngle: Angle(degrees: 0),
                    clockwise: false)

        // Right edge vertical line + rounded bottom-right corner
        path.addLine(to: CGPoint(x: bottomRight.x, y: bottomRight.y - cornerRadius))
        path.addArc(center: CGPoint(x: bottomRight.x - cornerRadius, y: bottomRight.y - cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: 0),
                    endAngle: Angle(degrees: 90),
                    clockwise: false)

        // Bottom edge line + rounded bottom-left corner
        path.addLine(to: CGPoint(x: bottomLeft.x + cornerRadius, y: bottomLeft.y))
        path.addArc(center: CGPoint(x: bottomLeft.x + cornerRadius, y: bottomLeft.y - cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: 90),
                    endAngle: Angle(degrees: 180),
                    clockwise: false)

        // Left edge vertical line + rounded top-left corner
        path.addLine(to: CGPoint(x: topLeft.x, y: topLeft.y + cornerRadius))
        path.addArc(center: CGPoint(x: topLeft.x + cornerRadius, y: topLeft.y + cornerRadius),
                    radius: cornerRadius,
                    startAngle: Angle(degrees: 180),
                    endAngle: Angle(degrees: 270),
                    clockwise: false)

        path.closeSubpath()

        return path
    }
}
